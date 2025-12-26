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


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JoinResponse(pydantic.BaseModel):
    game_id: str
    user_id: str = ""
    master_id: str = ""


@app.get("/join-as-master/{link}")
async def join_as_master_handler(link: str) -> JoinResponse:
    game = await database.Game.find_by_master_link(link)
    assert game

    master = await database.Master.find_by_id(game.master_id)
    assert master

    return JoinResponse(
        game_id=game.external_id,
        master_id=master.external_id,
    )


@app.get("/join/{link}")
async def join_as_character_handler(link: str) -> JoinResponse:
    cha = await database.Character.find_by_join_link(link)
    assert cha

    game = await database.Game.find_by_id(cha.game_id)
    assert game

    return JoinResponse(
        game_id=game.external_id,
        user_id=cha.external_id,
    )


@app.get("/game/{game_external_id}/map")
async def get_map_handler(game_external_id: str) -> database.Map:
    gmap = await database.Map.find_by_game_external_id(game_external_id)
    return gmap


@app.get("/game/{game_external_id}/character/{character_external_id}")
async def get_character_handler(
    game_external_id: str, character_external_id: str
) -> database.Character:
    logger.info(f"Game = {game_external_id}")
    cha = await database.Character.find_by_external_id(character_external_id)

    return cha


ACTIVE_CONNECTIONS: Dict[str, List[WebSocket]] = {}


@app.websocket("/ws/game/{game_external_id}/set")
async def set_map_stream_handler(game_external_id: str, websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        logger.info(f"WS data {data} for game {game_external_id}.")
        parsed_data = json.loads(data)

        topic = parsed_data["topic"]
        payload = parsed_data["data"]

        if topic == "map.update":
            x_center = payload["x_center"]
            y_center = payload["y_center"]
            zoom = payload["zoom"]

            gmap = await database.Map.find_by_game_external_id(game_external_id)

            gmap.x_center = x_center
            gmap.y_center = y_center
            gmap.zoom = zoom

            await gmap.save()

        player_websockets: List[WebSocket] = ACTIVE_CONNECTIONS.get(
            game_external_id, []
        )
        for player_ws in player_websockets:
            try:
                await player_ws.send_text(data)
            except Exception:
                player_websockets.remove(player_ws)


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
