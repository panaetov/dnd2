import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
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


@app.get("/game/{game_external_id}")
async def dummy_game_handler(game_external_id: str):
    return f"DUMMY GAME: {game_external_id}"
