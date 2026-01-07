import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, List

import pydantic
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

import database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel("INFO")


@asynccontextmanager
async def lifespan(*_, **__):
    await database.init_db()
    logger.info("Database is opened")
    yield
    await database.close_db()
    logger.info("Database is closed")


app = FastAPI(
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JoinResponse(pydantic.BaseModel):
    game_id: str
    user_id: str
    is_master: bool


@app.get("/api/join/{link}")
async def join_handler(link: str) -> JoinResponse:
    game = None
    master = None
    cha = None

    is_master = False
    user_id = ""
    if link.startswith("m-"):
        game = await database.Game.find_by_master_link(link)
        assert game

        master = await database.Master.find_by_id(game.master_id)
        assert master

        user_id = "master"
        is_master = True

    else:
        cha = await database.Character.find_by_join_link(link)
        assert cha

        game = await database.Game.find_by_id(cha.game_id)
        assert game

        user_id = cha.external_id
        is_master = False

    return JoinResponse(
        game_id=game.external_id,
        user_id=user_id,
        is_master=is_master,
    )


@app.get("/api/game/{game_external_id}/map")
async def get_map_handler(game_external_id: str) -> database.Map:
    gmap = await database.Map.find_by_game_external_id(game_external_id)
    return gmap


class CharacterFacade(pydantic.BaseModel):
    external_id: str
    avatar_url: str
    is_master: bool
    name: str


@app.get("/api/game/{game_external_id}/characters")
async def get_characters_handler(game_external_id: str) -> List[CharacterFacade]:
    logger.info(f"Game = {game_external_id}")
    game = await database.Game.find_by_external_id(game_external_id)

    characters = await database.Character.find_by_game_id(
        game.id,
    )
    results = []
    for cha in characters:
        results.append(
            CharacterFacade(
                external_id=cha.external_id,
                avatar_url=cha.avatar_url,
                is_master=False,
                name=cha.name,
            )
        )

    results.append(
        CharacterFacade(
            external_id="master",
            avatar_url=game.master_avatar_url,
            is_master=True,
            name="Мастер игры",
        )
    )
    return results


@app.get("/api/game/{game_external_id}/character/{character_external_id}")
async def get_character_handler(
    game_external_id: str, character_external_id: str
) -> CharacterFacade:
    logger.info(f"Game = {game_external_id}")
    game = await database.Game.find_by_external_id(game_external_id)
    if character_external_id == "master":
        return CharacterFacade(
            external_id="master",
            avatar_url=game.master_avatar_url,
        )

    cha = await database.Character.find_by_external_id(character_external_id)
    return CharacterFacade(
        external_id=cha.external_id,
        avatar_url=cha.avatar_url,
    )


ACTIVE_CONNECTIONS: Dict[str, List[WebSocket]] = {}


class MapUpdateRequest(pydantic.BaseModel):
    x_center: int | None = None
    y_center: int | None = None
    zoom: float | None = None


@app.post("/api/game/{game_external_id}/map")
async def update_map_handler(
    game_external_id: str, payload: MapUpdateRequest
) -> database.Map:
    x_center = payload.x_center
    y_center = payload.y_center
    zoom = payload.zoom

    gmap = await database.Map.find_by_game_external_id(game_external_id)

    if x_center is not None:
        gmap.x_center = x_center

    if y_center is not None:
        gmap.y_center = y_center

    if zoom is not None:
        gmap.zoom = zoom

    await gmap.save()

    player_websockets: List[WebSocket] = ACTIVE_CONNECTIONS.get(game_external_id, [])
    for player_ws in player_websockets:
        try:
            await player_ws.send_text(
                json.dumps(
                    {
                        "topic": "map.update",
                        "data": gmap.model_dump(),
                    }
                )
            )

        except Exception:
            player_websockets.remove(player_ws)

    return gmap


@app.websocket("/ws/game/{game_external_id}/get")
async def get_map_stream_handler(game_external_id: str, websocket: WebSocket):
    await websocket.accept()

    websockets = ACTIVE_CONNECTIONS.setdefault(game_external_id, [])

    logger.info(
        f"New connection for map updates: game={game_external_id}, "
        f"len(conns) = {len(websockets)}."
    )
    gmap = await database.Map.find_by_game_external_id(game_external_id)
    await websocket.send_text(
        json.dumps(
            {
                "topic": "map.update",
                "data": gmap.model_dump(),
            }
        )
    )

    websockets.append(websocket)
    while True:
        try:
            await websocket.receive_text()
        except Exception:
            logger.info(f"Connect from game {game_external_id} is closed")
            websockets.remove(websocket)
            break
