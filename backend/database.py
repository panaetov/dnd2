import datetime
import logging
import uuid
from typing import List, Optional

import asyncpg
from pydantic import BaseModel, Field

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
    login: str = ""
    password: str = ""

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

    @classmethod
    async def find_by_external_id(cls, external_id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM masters where external_id = $1;
                """,
                external_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def find_by_login(cls, login: str):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM masters where login = $1;
                """,
                login,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def create(cls, external_id: str, login: str, password: str):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO masters (external_id, login, password)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                external_id,
                login,
                password,
            )
            return cls(**dict(row))


class Game(BaseModel):
    id: int = 0
    name: str
    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    master_id: int
    master_join_link: str
    master_avatar_url: str
    room_id: int

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

    @classmethod
    async def find_by_room_id(cls, room_id: int):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM games where room_id = $1;
                """,
                str(room_id),
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def find_by_master_id(cls, master_id: int):
        async with _POOL.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM games
                WHERE master_id = $1
                ORDER BY id DESC
                """,
                master_id,
            )
            return [cls(**dict(row)) for row in rows]

    @classmethod
    async def create(
        cls,
        name: str,
        master_id: int,
        master_join_link: str,
        master_avatar_url: str,
        room_id: int,
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO games (
                    name,
                    external_id,
                    master_id,
                    master_join_link,
                    master_avatar_url,
                    room_id
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, name, external_id, master_id, master_join_link, master_avatar_url, room_id
                """,
                name,
                uuid.uuid4().hex,
                master_id,
                master_join_link,
                master_avatar_url,
                str(room_id),  # FIXME: в базе остался text
            )
            return cls(**dict(row))

    @classmethod
    async def update_master_avatar_url(
        cls, external_id: str, master_id: int, master_avatar_url: str
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE games
                SET master_avatar_url = $1
                WHERE external_id = $2 AND master_id = $3
                RETURNING id, name, external_id, master_id, master_join_link, master_avatar_url, room_id
                """,
                master_avatar_url,
                external_id,
                master_id,
            )
            return cls(**dict(row)) if row else None


class FogEracePoint(BaseModel):
    created_at: datetime.datetime | None = None
    x: float
    y: float
    map_id: int
    radius: int

    @classmethod
    async def add(cls, x, y, map_id, radius):
        async with _POOL.acquire() as conn:
            await conn.execute(
                """
                insert into fog_erace_points (
                    x, y, map_id, radius
                )
                values (
                    $1, $2, $3, $4
                )
                ON CONFLICT DO NOTHING;
                """,
                x,
                y,
                map_id,
                radius,
            )

    @classmethod
    async def find_by_map_external_id(cls, map_external_id):
        gmap = await Map.find_by_external_id(map_external_id)

        assert gmap

        return await cls.find_by_map_id(gmap.id)

    @classmethod
    async def find_by_map_id(cls, map_id):
        async with _POOL.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM fog_erace_points where map_id = $1
                order by created_at
                """,
                map_id,
            )
            return [cls(**dict(row)) for row in rows]

    @classmethod
    async def find_by_params(cls, x, y, map_id, radius):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM fog_erace_points
                WHERE x = $1 AND y = $2 AND map_id = $3 AND radius = $4
                """,
                x,
                y,
                map_id,
                radius,
            )
            return cls(**dict(row)) if row else None


class Character(BaseModel):
    id: int = 0
    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    name: str

    game_id: int
    join_link: str

    avatar_url: str
    race: str = "human"

    inventory: List = []
    color: str = "#ff0000"

    x: float | None = None
    y: float | None = None
    map_id: int | None = None

    async def save(self):
        async with _POOL.acquire() as conn:
            if self.id:
                await conn.execute(
                    """
                    update characters
                    set
                        x = $1,
                        y = $2
                    where
                        id = $3
                    """,
                    self.x,
                    self.y,
                    self.id,
                )

            else:
                raise NotImplementedError

        return self

    @classmethod
    async def create(
        cls,
        *,
        name: str,
        game_id: int,
        join_link: str,
        avatar_url: str,
        race: str = "human",
        color: str = "#ff0000",
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO characters (
                    external_id,
                    name,
                    game_id,
                    join_link,
                    avatar_url,
                    race,
                    color
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                uuid.uuid4().hex,
                name,
                game_id,
                join_link,
                avatar_url,
                race,
                color,
            )
            return cls(**dict(row))

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

    @classmethod
    async def find_by_game_id(cls, game_id):
        async with _POOL.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM characters where game_id = $1;
                """,
                game_id,
            )
            return [cls(**dict(row)) for row in rows]

    @classmethod
    async def update_by_external_id_and_game_id(
        cls,
        *,
        external_id: str,
        game_id: int,
        name: str | None = None,
        avatar_url: str | None = None,
        race: str | None = None,
        color: str | None = None,
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE characters
                SET
                    name = COALESCE($1, name),
                    avatar_url = COALESCE($2, avatar_url),
                    race = COALESCE($3, race),
                    color = COALESCE($4, color)
                WHERE external_id = $5 AND game_id = $6
                RETURNING *
                """,
                name,
                avatar_url,
                race,
                color,
                external_id,
                game_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def delete_by_external_id_and_game_id(cls, external_id: str, game_id: int) -> bool:
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                DELETE FROM characters
                WHERE external_id = $1 AND game_id = $2
                RETURNING id
                """,
                external_id,
                game_id,
            )
            return row is not None


class Map(BaseModel):
    id: int = 0

    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    game_id: int
    url: str

    x_center: float
    y_center: float
    zoom: float

    async def save(self):
        async with _POOL.acquire() as conn:
            if self.id:
                await conn.execute(
                    """
                    update maps
                    set
                        external_id = $1,
                        game_id = $2,
                        url = $3,
                        x_center = $4,
                        y_center = $5,
                        zoom = $6
                    where
                        id = $7
                    """,
                    self.external_id,
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
                        external_id,
                        game_id,
                        url,
                        x_center,
                        y_center,
                        zoom
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    self.external_id,
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


class Item(BaseModel):
    id: int = 0

    name: str
    game_id: int
    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    map_id: int | None = None
    x: float | None = None
    y: float | None = None

    icon_url: str

    async def save(self):
        async with _POOL.acquire() as conn:
            if self.id:
                await conn.execute(
                    """
                    update items
                    set
                        name = $1,
                        game_id = $2,
                        external_id = $3,
                        x = $4,
                        y = $5,
                        icon_url = $6,
                        map_id = $8
                    where
                        id = $7
                    """,
                    self.name,
                    self.game_id,
                    self.external_id,
                    self.x,
                    self.y,
                    self.icon_url,
                    self.id,
                    self.map_id,
                )

            else:
                raise NotImplementedError

        return self

    @classmethod
    async def create(
        cls,
        *,
        name: str,
        game_id: int,
        icon_url: str,
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO items (
                    external_id,
                    name,
                    game_id,
                    icon_url,
                    map_id,
                    x,
                    y
                )
                VALUES ($1, $2, $3, $4, NULL, NULL, NULL)
                RETURNING *
                """,
                uuid.uuid4().hex,
                name,
                game_id,
                icon_url,
            )
            return cls(**dict(row))

    @classmethod
    async def find_by_external_id(cls, external_id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM items where external_id = $1;
                """,
                external_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def find_by_game_external_id(cls, game_external_id):
        game = await Game.find_by_external_id(game_external_id)

        assert game

        return await cls.find_by_game_id(game.id)

    @classmethod
    async def find_by_game_id(cls, game_id):
        async with _POOL.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM items where game_id = $1;
                """,
                game_id,
            )
            return [cls(**dict(row)) for row in rows]

    @classmethod
    async def update_by_external_id_and_game_id(
        cls,
        *,
        external_id: str,
        game_id: int,
        name: str | None = None,
        icon_url: str | None = None,
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE items
                SET
                    name = COALESCE($1, name),
                    icon_url = COALESCE($2, icon_url)
                WHERE external_id = $3 AND game_id = $4
                RETURNING *
                """,
                name,
                icon_url,
                external_id,
                game_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def delete_by_external_id_and_game_id(cls, external_id: str, game_id: int) -> bool:
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                DELETE FROM items
                WHERE external_id = $1 AND game_id = $2
                RETURNING id
                """,
                external_id,
                game_id,
            )
            return row is not None


class AudioFile(BaseModel):
    id: int = 0
    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str
    game_id: int
    url: str
    duration_seconds: float

    @classmethod
    async def create(
        cls,
        *,
        name: str,
        game_id: int,
        url: str,
        duration_seconds: float,
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO audio_files (
                    external_id,
                    name,
                    game_id,
                    url,
                    duration_seconds
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                uuid.uuid4().hex,
                name,
                game_id,
                url,
                duration_seconds,
            )
            return cls(**dict(row))

    @classmethod
    async def find_by_external_id(cls, external_id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM audio_files where external_id = $1;
                """,
                external_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def find_by_game_id(cls, game_id):
        async with _POOL.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audio_files where game_id = $1;
                """,
                game_id,
            )
            return [cls(**dict(row)) for row in rows]

    @classmethod
    async def update_by_external_id_and_game_id(
        cls,
        *,
        external_id: str,
        game_id: int,
        name: str | None = None,
        url: str | None = None,
        duration_seconds: float | None = None,
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE audio_files
                SET
                    name = COALESCE($1, name),
                    url = COALESCE($2, url),
                    duration_seconds = COALESCE($3, duration_seconds)
                WHERE external_id = $4 AND game_id = $5
                RETURNING *
                """,
                name,
                url,
                duration_seconds,
                external_id,
                game_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def delete_by_external_id_and_game_id(cls, external_id: str, game_id: int) -> bool:
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                DELETE FROM audio_files
                WHERE external_id = $1 AND game_id = $2
                RETURNING id
                """,
                external_id,
                game_id,
            )
            return row is not None


class VideoFile(BaseModel):
    id: int = 0
    external_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str
    game_id: int
    url: str
    duration_seconds: float

    @classmethod
    async def create(
        cls,
        *,
        name: str,
        game_id: int,
        url: str,
        duration_seconds: float,
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO video_files (
                    external_id,
                    name,
                    game_id,
                    url,
                    duration_seconds
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                uuid.uuid4().hex,
                name,
                game_id,
                url,
                duration_seconds,
            )
            return cls(**dict(row))

    @classmethod
    async def find_by_external_id(cls, external_id):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM video_files where external_id = $1;
                """,
                external_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def find_by_game_id(cls, game_id):
        async with _POOL.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM video_files where game_id = $1;
                """,
                game_id,
            )
            return [cls(**dict(row)) for row in rows]

    @classmethod
    async def update_by_external_id_and_game_id(
        cls,
        *,
        external_id: str,
        game_id: int,
        name: str | None = None,
        url: str | None = None,
        duration_seconds: float | None = None,
    ):
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE video_files
                SET
                    name = COALESCE($1, name),
                    url = COALESCE($2, url),
                    duration_seconds = COALESCE($3, duration_seconds)
                WHERE external_id = $4 AND game_id = $5
                RETURNING *
                """,
                name,
                url,
                duration_seconds,
                external_id,
                game_id,
            )
            return cls(**dict(row)) if row else None

    @classmethod
    async def delete_by_external_id_and_game_id(cls, external_id: str, game_id: int) -> bool:
        async with _POOL.acquire() as conn:
            row = await conn.fetchrow(
                """
                DELETE FROM video_files
                WHERE external_id = $1 AND game_id = $2
                RETURNING id
                """,
                external_id,
                game_id,
            )
            return row is not None
