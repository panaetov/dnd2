import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse

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


@app.get("/join-as-master/{link}")
async def join_as_master_handler(link: str, response: Response):
    game = await database.Game.find_by_master_link(link)
    assert game

    master = await database.Master.find_by_id(game.master_id)
    assert master

    response = RedirectResponse(f"/{game.external_id}")

    response.set_cookie(key="game_id", value=game.external_id)
    response.set_cookie(key="user_id", value=f"m:{master.external_id}")
    return response


@app.get("/join/{link}")
async def join_as_character_handler(link: str, response: Response):
    cha = await database.Character.find_by_join_link(link)
    assert cha

    game = await database.Game.find_by_id(cha.game_id)
    assert game

    response = RedirectResponse(f"/{game.external_id}")

    response.set_cookie(key="game_id", value=game.external_id)
    response.set_cookie(key="user_id", value=f"c:{cha.external_id}")
    return response


@app.get("/game/{game_external_id}/map")
async def get_map_handler(game_external_id: str):
    gmap = await database.Map.find_by_game_external_id(game_external_id)
    return gmap.model_dump()


@app.get("/game/{game_external_id}/character/{character_external_id}")
async def get_character_handler(game_external_id: str, character_external_id: str):
    logger.info(f"Game = {game_external_id}")
    cha = await database.Character.find_by_external_id(character_external_id)

    return cha.model_dump()


ACTIVE_CONNECTIONS: Dict[str, List[WebSocket]] = {}


@app.websocket("/ws/game/{game_external_id}/map/set")
async def set_map_stream_handler(game_external_id: str, websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        logger.info(f"New map data {data} for game {game_external_id}.")
        parsed_data = json.loads(data)
        x_center = parsed_data["x_center"]
        y_center = parsed_data["y_center"]
        zoom = parsed_data["zoom"]

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
                await player_ws.send_text(
                    json.dumps(
                        {
                            "data": gmap.model_dump(),
                        }
                    )
                )
            except WebSocketDisconnect:
                player_websockets.remove(player_ws)


@app.websocket("/ws/game/{game_external_id}/map/get")
async def get_map_stream_handler(game_external_id: str, websocket: WebSocket):
    await websocket.accept()

    websockets = ACTIVE_CONNECTIONS.setdefault(game_external_id, [])

    logger.info(
        f"New connection for map updates: game={game_external_id}, len(conns) = {len(websockets)}."
    )
    gmap = await database.Map.find_by_game_external_id(game_external_id)
    await websocket.send_text(
        json.dumps(
            {
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
