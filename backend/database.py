import datetime
import json
import logging
import uuid
from typing import Annotated, Any, List, Optional

import asyncpg
from pydantic import BaseModel, BeforeValidator, Field

import settings

logger = logging.getLogger(__name__)


_POOL: Optional[asyncpg.Pool] = None


async def init_db():
    logger.info(f"Connecting to database: {settings.DB_CONFIG}")
    global _POOL
    _POOL = await asyncpg.create_pool(**settings.DB_CONFIG)


async def close_db():
    if _POOL:
        await _POOL.close()


class Master(BaseModel):
    id: int = 0
    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    @classmethod
    async def find_by_id(cls, id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM masters where id = $1;
                """,
                id,
            )
            return cls(**dict(row)) if row else None


class Game(BaseModel):
    id: int = 0
    name: str
    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    master_id: int
    master_join_link: str

    @classmethod
    async def find_by_external_id(cls, external_id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM games where external_id = $1;
                """,
                external_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def find_by_id(cls, id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM games where id = $1;
                """,
                id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def find_by_master_link(cls, master_join_link):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM games where master_join_link = $1;
                """,
                master_join_link,
            )
            return cls(**dict(row)) if row else None


class Character(BaseModel):
    id: int = 0
    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    name: str

    game_id: int
    join_link: str

    avatar_url: str
    race: str

    @classmethod
    async def find_by_join_link(cls, join_link):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM characters where join_link = $1;
                """,
                join_link,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def find_by_external_id(cls, external_id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM characters where external_id = $1;
                """,
                external_id,
            )
            return cls(**dict(row)) if row else None


class Map(BaseModel):
    id: int = 0

    game_id: int
    url: str

    x_center: int
    y_center: int
    zoom: float

    async def save(self):
        async with _POOL.acquire() as conn:
            if self.id:
                await conn.execute(
                    """
                    update maps
                    set
                        game_id = $1,
                        url = $2,
                        x_center = $3,
                        y_center = $4,
                        zoom = $5
                    where
                        id = $6
                    """,
                    self.game_id,
                    self.url,
                    self.x_center,
                    self.y_center,
                    self.zoom,
                    self.id,
                )

            else:
                new_row = await conn.fetchrow(
                    """
                    INSERT INTO maps (
                        game_id,
                        url,
                        x_center,
                        y_center,
                        zoom
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    self.game_id,
                    self.url,
                    self.x_center,
                    self.y_center,
                    self.zoom,
                )
                self.id = new_row["id"]

        return self

    @classmethod
    async def find_by_game_external_id(cls, game_external_id):
        game = await Game.find_by_external_id(game_external_id)

        assert game

        return await cls.find_by_game_id(game.id)

    @classmethod
    async def find_by_game_id(cls, game_id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM maps where game_id = $1;
                """,
                game_id,
            )
            return cls(**dict(row)) if row else None
