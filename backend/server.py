import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, List

import pydantic
from aiortc import RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from janus_client import JanusSession, JanusVideoRoomPlugin

import database
import settings

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
    room_id: int
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
        room_id=game.room_id,
    )


@app.get("/api/game/{game_external_id}/map")
async def get_map_handler(game_external_id: str) -> database.Map:
    gmap = await database.Map.find_by_game_external_id(game_external_id)
    return gmap


class ItemFacade(pydantic.BaseModel):
    external_id: str

    name: str

    icon_url: str = ''
    x: float | None = None
    y: float | None = None


@app.get("/api/game/{game_external_id}/items")
async def get_items_handler(game_external_id: str) -> List[ItemFacade]:
    logger.info(f"Game = {game_external_id}")
    game = await database.Game.find_by_external_id(game_external_id)

    items = await database.Item.find_by_game_id(
        game.id,
    )
    results = []
    for item in items:
        results.append(
            ItemFacade(
                external_id=item.external_id,
                name=item.name,
                x=item.x,
                y=item.y,
                icon_url=item.icon_url,
            )
        )

    return results


class ItemChangedRequest(pydantic.BaseModel):
    x: float | None = None
    y: float | None = None


@app.post("/api/game/{game_external_id}/item/{item_external_id}")
async def item_changed_handler(
    game_external_id: str, item_external_id: str, payload: ItemChangedRequest
) -> ItemFacade:
    item = await database.Item.find_by_external_id(item_external_id)
    assert item

    item.x = payload.x
    item.y = payload.y

    await item.save()

    player_websockets: List[WebSocket] = ACTIVE_CONNECTIONS.get(game_external_id, [])
    for player_ws in player_websockets:
        try:
            await player_ws.send_text(
                json.dumps(
                    {
                        "topic": "item.update",
                        "data": {
                            "external_id": item.external_id,
                            "x": item.x,
                            "y": item.y,
                        },
                    }
                )
            )

        except Exception:
            logger.exception("Connection is lost")
            player_websockets.remove(player_ws)

    return ItemFacade(
        external_id=item.external_id,
        name=item.name,
        x=item.x,
        y=item.y,
        icon_url=item.icon_url,
    )


class InventoryItem(pydantic.BaseModel):
    id: str
    name: str
    image_url: str
    description: str
    quantity: int


class CharacterFacade(pydantic.BaseModel):
    external_id: str
    avatar_url: str
    is_master: bool
    name: str
    color: str = "#ffffff"
    inventory: List[InventoryItem] = []
    x: float | None = None
    y: float | None = None


class CharacterUpdateRequest(pydantic.BaseModel):
    x: float | None = None
    y: float | None = None


@app.post("/api/game/{game_external_id}/character/{character_external_id}")
async def update_map_handler(
    game_external_id: str, character_external_id, payload: CharacterUpdateRequest
):
    x = payload.x
    y = payload.y

    cha = await database.Character.find_by_external_id(character_external_id)
    cha.x = x
    cha.y = y

    await cha.save()

    player_websockets: List[WebSocket] = ACTIVE_CONNECTIONS.get(game_external_id, [])
    for player_ws in player_websockets:
        try:
            await player_ws.send_text(
                json.dumps(
                    {
                        "topic": "character.update",
                        "data": {
                            "external_id": cha.external_id,
                            "x": x,
                            "y": y,
                        },
                    }
                )
            )

        except Exception:
            logger.exception("Connection is lost")
            player_websockets.remove(player_ws)

    return {}


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
                color=cha.color,
                inventory=cha.inventory,
                x=cha.x,
                y=cha.y,
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
            is_master=True,
            name="Мастер игры",
        )

    cha = await database.Character.find_by_external_id(character_external_id)
    return CharacterFacade(
        external_id=cha.external_id,
        avatar_url=cha.avatar_url,
        is_master=False,
        name=cha.name,
        color=cha.color,
        inventory=cha.inventory,
        x=cha.x,
        y=cha.y,
    )


ACTIVE_CONNECTIONS: Dict[str, List[WebSocket]] = {}

# Хранилище активных audio plugins: ключ - f"{game_external_id}:{audio_external_id}", значение - (plugin, session, task)
ACTIVE_AUDIO_PLUGINS: Dict[str, tuple] = {}

# Хранилище активных video plugins: ключ - f"{game_external_id}:{video_external_id}", значение - (plugin, session, task)
ACTIVE_VIDEO_PLUGINS: Dict[str, tuple] = {}


class DiceStartedRequest(pydantic.BaseModel):
    dice_id: str


@app.post("/api/game/{game_external_id}/dice/started")
async def dice_started_handler(game_external_id: str, payload: DiceStartedRequest):
    player_websockets: List[WebSocket] = ACTIVE_CONNECTIONS.get(game_external_id, [])
    for player_ws in player_websockets:
        try:
            await player_ws.send_text(
                json.dumps(
                    {
                        "topic": "dice.start",
                        "data": {
                            "dice_id": payload.dice_id,
                        },
                    }
                )
            )

        except Exception:
            logger.exception("Connection is lost")
            player_websockets.remove(player_ws)

    return {}


class DiceChangedRequest(pydantic.BaseModel):
    new_dice_id: str


@app.post("/api/game/{game_external_id}/dice/changed")
async def dice_changed_handler(game_external_id: str, payload: DiceChangedRequest):
    player_websockets: List[WebSocket] = ACTIVE_CONNECTIONS.get(game_external_id, [])
    for player_ws in player_websockets:
        try:
            await player_ws.send_text(
                json.dumps(
                    {
                        "topic": "dice.change",
                        "data": {
                            "new_dice_id": payload.new_dice_id,
                        },
                    }
                )
            )

        except Exception:
            logger.exception("Connection is lost")
            player_websockets.remove(player_ws)

    return {}


class DiceResultedRequest(pydantic.BaseModel):
    dice_id: str
    result: int


@app.post("/api/game/{game_external_id}/dice/resulted")
async def dice_resulted_handler(game_external_id: str, payload: DiceResultedRequest):
    player_websockets: List[WebSocket] = ACTIVE_CONNECTIONS.get(game_external_id, [])
    for player_ws in player_websockets:
        try:
            await player_ws.send_text(
                json.dumps(
                    {
                        "topic": "dice.result",
                        "data": {
                            "dice_id": payload.dice_id,
                            "result": payload.result,
                        },
                    }
                )
            )

        except Exception:
            logger.exception("Connection is lost")
            player_websockets.remove(player_ws)

    return {}


class MapUpdateRequest(pydantic.BaseModel):
    x_center: float | None = None
    y_center: float | None = None
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
        logger.info(f"Sending updates to player.")
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
            logger.exception("Cannot send updates to ws, closing ws.")
            player_websockets.remove(player_ws)

    return gmap


class FogEracePointFacade(pydantic.BaseModel):
    x: float
    y: float
    map_external_id: str
    radius: int
    created_at: str | None = None


class FogEracePointCreateRequest(pydantic.BaseModel):
    x: float
    y: float
    radius: int


@app.post("/api/game/{game_external_id}/fog-erace-point")
async def create_fog_erace_point_handler(
    game_external_id: str, payload: FogEracePointCreateRequest
) -> FogEracePointFacade:
    gmap = await database.Map.find_by_game_external_id(game_external_id)
    assert gmap

    await database.FogEracePoint.add(payload.x, payload.y, gmap.id, payload.radius)

    fog_point = await database.FogEracePoint.find_by_params(
        payload.x, payload.y, gmap.id, payload.radius
    )
    assert fog_point

    player_websockets: List[WebSocket] = ACTIVE_CONNECTIONS.get(game_external_id, [])
    for player_ws in player_websockets:
        try:
            await player_ws.send_text(
                json.dumps(
                    {
                        "topic": "fog_erace_point.add",
                        "data": {
                            "x": fog_point.x,
                            "y": fog_point.y,
                            "map_external_id": gmap.external_id,
                            "radius": fog_point.radius,
                            "created_at": (
                                fog_point.created_at.isoformat()
                                if fog_point.created_at
                                else None
                            ),
                        },
                    }
                )
            )

        except Exception:
            logger.exception("Connection is lost")
            player_websockets.remove(player_ws)

    return FogEracePointFacade(
        x=fog_point.x,
        y=fog_point.y,
        map_external_id=gmap.external_id,
        radius=fog_point.radius,
        created_at=(fog_point.created_at.isoformat() if fog_point.created_at else None),
    )


@app.get("/api/game/{game_external_id}/fog-erace-points")
async def get_fog_erace_points_handler(
    game_external_id: str,
) -> List[FogEracePointFacade]:
    gmap = await database.Map.find_by_game_external_id(game_external_id)
    assert gmap

    fog_points = await database.FogEracePoint.find_by_map_id(gmap.id)

    results = []
    for fog_point in fog_points:
        results.append(
            FogEracePointFacade(
                x=fog_point.x,
                y=fog_point.y,
                map_external_id=gmap.external_id,
                radius=fog_point.radius,
                created_at=(
                    fog_point.created_at.isoformat() if fog_point.created_at else None
                ),
            )
        )

    return results


class AudioFileFacade(pydantic.BaseModel):
    external_id: str
    name: str


class VideoFileFacade(pydantic.BaseModel):
    external_id: str
    name: str


@app.get("/api/game/{game_external_id}/audio-files")
async def get_audio_files_handler(
    game_external_id: str,
) -> List[AudioFileFacade]:
    game = await database.Game.find_by_external_id(game_external_id)
    assert game

    audio_files = await database.AudioFile.find_by_game_id(game.id)

    results = []
    for audio_file in audio_files:
        results.append(
            AudioFileFacade(
                external_id=audio_file.external_id,
                name=audio_file.name,
            )
        )

    return results


@app.get("/api/game/{game_external_id}/video-files")
async def get_video_files_handler(
    game_external_id: str,
) -> List[VideoFileFacade]:
    game = await database.Game.find_by_external_id(game_external_id)
    assert game

    video_files = await database.VideoFile.find_by_game_id(game.id)

    results = []
    for video_file in video_files:
        results.append(
            VideoFileFacade(
                external_id=video_file.external_id,
                name=video_file.name,
            )
        )

    return results


async def play_audio_in_room(
    audio_url: str,
    room_id: int,
    game_external_id: str,
    audio_external_id: str,
    duration_seconds: float | None = None,
    display_name: str = "Audio Player",
    volume: float = 1.0,
):
    """Проигрывает аудио файл в Janus комнате в фоновой корутине"""
    plugin_key = f"{game_external_id}:{audio_external_id}"
    plugin = None
    session = None
    try:
        # Создаем список ICE серверов со всеми TURN серверами
        ice_servers = [
            RTCIceServer(
                urls=turn_url,
                username=settings.TURN_SERVER_USERNAME,
                credential=settings.TURN_SERVER_CREDENTIAL,
            )
            for turn_url in settings.TURN_SERVERS
        ]
        # Добавляем STUN сервер
        ice_servers.append(RTCIceServer(urls=settings.STUN_SERVER_URL))

        config = RTCConfiguration(iceServers=ice_servers)
        session = JanusSession(base_url=settings.JANUS_URL)
        plugin = JanusVideoRoomPlugin(pc_config=config)

        # Attach to Janus session
        await plugin.attach(session=session)
        await plugin.join_as_publisher(room_id=room_id, display=display_name)

        logger.info(
            f"Starting audio playback: {audio_url} in room {room_id} with volume {volume}"
        )

        # Prepare media player с настройкой громкости через ffmpeg фильтр
        player_options = {}
        if volume != 1.0:
            # Применяем фильтр громкости через ffmpeg
            player_options = {"-af": f"volume={volume}"}

        player = MediaPlayer(audio_url, options=player_options)
        await plugin.publish(player, bitrate=2000000)

        # Сохраняем plugin и session в глобальную переменную
        task = asyncio.current_task()
        ACTIVE_AUDIO_PLUGINS[plugin_key] = (plugin, session, task)

        # Wait for audio to finish
        if duration_seconds is not None:
            logger.info(f"Waiting {duration_seconds} seconds for audio to finish")
            await asyncio.sleep(duration_seconds)
        else:
            # If duration is not specified, wait indefinitely until cancelled
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info(f"Audio playback cancelled for room {room_id}")

        # Удаляем из активных после завершения
        if plugin_key in ACTIVE_AUDIO_PLUGINS:
            del ACTIVE_AUDIO_PLUGINS[plugin_key]

        await plugin.leave()
        await plugin.destroy()
        await session.destroy()

        logger.info(f"Audio playback finished for room {room_id}")
    except asyncio.CancelledError:
        logger.info(f"Audio playback task cancelled for {plugin_key}")
        # Удаляем из активных при отмене
        if plugin_key in ACTIVE_AUDIO_PLUGINS:
            del ACTIVE_AUDIO_PLUGINS[plugin_key]
        if plugin:
            try:
                await plugin.leave()
                await plugin.destroy()
            except Exception:
                pass
        if session:
            try:
                await session.destroy()
            except Exception:
                pass
    except Exception as e:
        logger.exception(f"Error playing audio in room {room_id}: {e}")
        # Удаляем из активных при ошибке
        if plugin_key in ACTIVE_AUDIO_PLUGINS:
            del ACTIVE_AUDIO_PLUGINS[plugin_key]


async def play_video_in_room(
    video_url: str,
    room_id: int,
    game_external_id: str,
    video_external_id: str,
    duration_seconds: float | None = None,
    display_name: str = "Video Player",
):
    """Проигрывает видео файл в Janus комнате в фоновой корутине"""
    plugin_key = f"{game_external_id}:{video_external_id}"
    plugin = None
    session = None
    try:
        # Создаем список ICE серверов со всеми TURN серверами
        ice_servers = [
            RTCIceServer(
                urls=turn_url,
                username=settings.TURN_SERVER_USERNAME,
                credential=settings.TURN_SERVER_CREDENTIAL,
            )
            for turn_url in settings.TURN_SERVERS
        ]
        # Добавляем STUN сервер
        ice_servers.append(RTCIceServer(urls=settings.STUN_SERVER_URL))

        config = RTCConfiguration(iceServers=ice_servers)
        session = JanusSession(base_url=settings.JANUS_URL)
        plugin = JanusVideoRoomPlugin(pc_config=config)

        # Attach to Janus session
        await plugin.attach(session=session)
        await plugin.join_as_publisher(room_id=room_id, display=display_name)

        logger.info(f"Starting video playback: {video_url} in room {room_id}")

        player = MediaPlayer(video_url)
        await plugin.publish(
            player=player,
            bitrate=2000000,
            trickle=True,
        )
        logger.info("Plugin pulished.")
        logger.info("Player published.")

        # Сохраняем plugin и session в глобальную переменную
        task = asyncio.current_task()
        ACTIVE_VIDEO_PLUGINS[plugin_key] = (plugin, session, task)

        # Wait for video to finish
        if duration_seconds is not None:
            logger.info(f"Waiting {duration_seconds} seconds for video to finish")
            await asyncio.sleep(duration_seconds)
        else:
            # If duration is not specified, wait indefinitely until cancelled
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info(f"Video playback cancelled for room {room_id}")

        # Удаляем из активных после завершения
        if plugin_key in ACTIVE_VIDEO_PLUGINS:
            del ACTIVE_VIDEO_PLUGINS[plugin_key]

        await plugin.leave()
        await plugin.destroy()
        await session.destroy()

        logger.info(f"Video playback finished for room {room_id}")
    except asyncio.CancelledError:
        logger.info(f"Video playback task cancelled for {plugin_key}")
        # Удаляем из активных при отмене
        if plugin_key in ACTIVE_VIDEO_PLUGINS:
            del ACTIVE_VIDEO_PLUGINS[plugin_key]
        if plugin:
            try:
                await plugin.leave()
                await plugin.destroy()
            except Exception:
                pass
        if session:
            try:
                await session.destroy()
            except Exception:
                pass
    except Exception as e:
        logger.exception(f"Error playing video in room {room_id}: {e}")
        # Удаляем из активных при ошибке
        if plugin_key in ACTIVE_VIDEO_PLUGINS:
            del ACTIVE_VIDEO_PLUGINS[plugin_key]


class PlayAudioRequest(pydantic.BaseModel):
    audio_external_id: str
    volume: float = 1.0  # Громкость от 0.0 до 1.0, по умолчанию 1.0 (100%)


class PlayVideoRequest(pydantic.BaseModel):
    video_external_id: str


@app.post("/api/game/{game_external_id}/audio/play")
async def play_audio_handler(game_external_id: str, payload: PlayAudioRequest) -> dict:
    game = await database.Game.find_by_external_id(game_external_id)
    assert game
    assert game.room_id is not None, "Game room_id is not set"

    audio_file = await database.AudioFile.find_by_external_id(payload.audio_external_id)
    assert (
        audio_file
    ), f"Audio file with external_id {payload.audio_external_id} not found"
    assert audio_file.game_id == game.id, "Audio file does not belong to this game"

    # Проверяем диапазон громкости
    if not (0.0 <= payload.volume <= 1.0):
        return {"status": "error", "message": "Volume must be between 0.0 and 1.0"}

    # Запускаем проигрывание аудио в фоновой корутине
    asyncio.create_task(
        play_audio_in_room(
            audio_url=audio_file.url,
            room_id=game.room_id,
            game_external_id=game_external_id,
            audio_external_id=audio_file.external_id,
            duration_seconds=audio_file.duration_seconds,
            display_name=f"Audio: {audio_file.name}",
            volume=payload.volume,
        )
    )

    logger.info(
        f"Started audio playback: {audio_file.name} (external_id: {audio_file.external_id}) "
        f"in game {game_external_id}, room {game.room_id}"
    )

    return {"status": "started", "audio_external_id": audio_file.external_id}


@app.post("/api/game/{game_external_id}/audio/stop")
async def stop_audio_handler(game_external_id: str, payload: PlayAudioRequest) -> dict:
    game = await database.Game.find_by_external_id(game_external_id)
    assert game

    audio_file = await database.AudioFile.find_by_external_id(payload.audio_external_id)
    assert (
        audio_file
    ), f"Audio file with external_id {payload.audio_external_id} not found"
    assert audio_file.game_id == game.id, "Audio file does not belong to this game"

    # Ищем активное проигрывание по паре game_external_id + audio_external_id
    plugin_key = f"{game_external_id}:{payload.audio_external_id}"

    if plugin_key not in ACTIVE_AUDIO_PLUGINS:
        return {
            "status": "not_found",
            "message": "Audio playback not found or already stopped",
        }

    plugin, session, task = ACTIVE_AUDIO_PLUGINS[plugin_key]

    try:
        # Отменяем задачу проигрывания
        if task and not task.done():
            task.cancel()

        # Останавливаем plugin
        await plugin.leave()
        await plugin.destroy()

        # Уничтожаем session
        await session.destroy()

        # Удаляем из активных
        del ACTIVE_AUDIO_PLUGINS[plugin_key]

        logger.info(
            f"Stopped audio playback: {audio_file.name} (external_id: {audio_file.external_id}) "
            f"in game {game_external_id}"
        )

        return {"status": "stopped", "audio_external_id": audio_file.external_id}
    except Exception as e:
        logger.exception(f"Error stopping audio playback: {e}")
        # Удаляем из активных даже при ошибке
        if plugin_key in ACTIVE_AUDIO_PLUGINS:
            del ACTIVE_AUDIO_PLUGINS[plugin_key]
        return {"status": "error", "message": str(e)}


@app.post("/api/game/{game_external_id}/video/play")
async def play_video_handler(game_external_id: str, payload: PlayVideoRequest) -> dict:
    game = await database.Game.find_by_external_id(game_external_id)
    assert game
    assert game.room_id is not None, "Game room_id is not set"

    video_file = await database.VideoFile.find_by_external_id(payload.video_external_id)
    assert (
        video_file
    ), f"Video file with external_id {payload.video_external_id} not found"
    assert video_file.game_id == game.id, "Video file does not belong to this game"

    # Запускаем проигрывание видео в фоновой корутине
    asyncio.create_task(
        play_video_in_room(
            video_url=video_file.url,
            room_id=game.room_id,
            game_external_id=game_external_id,
            video_external_id=video_file.external_id,
            duration_seconds=video_file.duration_seconds,
        )
    )

    logger.info(
        f"Started video playback: {video_file.name} (external_id: {video_file.external_id}) "
        f"in game {game_external_id}, room {game.room_id}"
    )

    return {"status": "started", "video_external_id": video_file.external_id}


@app.post("/api/game/{game_external_id}/video/stop")
async def stop_video_handler(game_external_id: str, payload: PlayVideoRequest) -> dict:
    game = await database.Game.find_by_external_id(game_external_id)
    assert game

    video_file = await database.VideoFile.find_by_external_id(payload.video_external_id)
    assert (
        video_file
    ), f"Video file with external_id {payload.video_external_id} not found"
    assert video_file.game_id == game.id, "Video file does not belong to this game"

    plugin_key = f"{game_external_id}:{video_file.external_id}"

    if plugin_key not in ACTIVE_VIDEO_PLUGINS:
        return {
            "status": "not_found",
            "message": "Video playback not found or already stopped",
        }

    plugin, session, task = ACTIVE_VIDEO_PLUGINS[plugin_key]

    try:
        # Отменяем задачу проигрывания
        if task and not task.done():
            task.cancel()

        # Останавливаем plugin
        await plugin.leave()
        await plugin.destroy()

        # Уничтожаем session
        await session.destroy()

        # Удаляем из активных
        del ACTIVE_VIDEO_PLUGINS[plugin_key]

        logger.info(
            f"Stopped video playback: {video_file.name} (external_id: {video_file.external_id}) "
            f"in game {game_external_id}"
        )

        return {"status": "stopped", "video_external_id": video_file.external_id}
    except Exception as e:
        logger.exception(f"Error stopping video playback: {e}")
        # Удаляем из активных даже при ошибке
        if plugin_key in ACTIVE_VIDEO_PLUGINS:
            del ACTIVE_VIDEO_PLUGINS[plugin_key]
        return {"status": "error", "message": str(e)}


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
            logger.info("Looping ws connection...")
            await websocket.receive_text()
        except Exception:
            logger.info(f"Connect from game {game_external_id} is closed")
            websockets.remove(websocket)
            break
