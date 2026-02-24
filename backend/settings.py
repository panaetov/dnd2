import os

DATABASE_HOST = os.environ.get("SERVICE_DATABASE_HOST", "db")
DATABASE_NAME = os.environ.get("SERVICE_DATABASE_NAME", "dnd")
DATABASE_PORT = int(os.environ.get("SERVICE_DATABASE_PORT", "5432"))

DATABASE_DSN = (
    f"postgresql+asyncpg://dude:dude_password_123@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

MASTER_DEFAULT_AVATAR = (
    "https://storage.yandexcloud.net/dnd2/demo-game-1/master-avatar.jpg"
)

DB_CONFIG = {
    "host": DATABASE_HOST,
    "port": DATABASE_PORT,
    "user": "dude",
    "password": "dude_password_123",
    "database": DATABASE_NAME,
}

JANUS_URL = os.environ.get("JANUS_URL", "http://51.250.102.96:8088/janus")

TURN_SERVER_USERNAME = os.environ.get("TURN_SERVER_USERNAME", "000000002084126365")
TURN_SERVER_CREDENTIAL = os.environ.get(
    "TURN_SERVER_CREDENTIAL", "4kbbi1XtfrmjnuxOkgfmU1gF6zw="
)

STUN_SERVER_URL = os.environ.get("STUN_SERVER_URL", "stun:stun.l.google.com:19302")

MASTER_CABINET_JWT_SECRET = os.environ.get(
    "MASTER_CABINET_JWT_SECRET", "change-this-master-cabinet-jwt-secret"
)
MASTER_CABINET_JWT_ALGORITHM = os.environ.get("MASTER_CABINET_JWT_ALGORITHM", "HS256")
MASTER_CABINET_JWT_EXPIRE_SECONDS = int(
    os.environ.get("MASTER_CABINET_JWT_EXPIRE_SECONDS", "604800")
)
MASTER_CABINET_AUTH_COOKIE_NAME = os.environ.get(
    "MASTER_CABINET_AUTH_COOKIE_NAME", "master_cabinet_token"
)
MASTER_CABINET_AUTH_COOKIE_SECURE = (
    os.environ.get("MASTER_CABINET_AUTH_COOKIE_SECURE", "false").lower() == "true"
)
MASTER_CABINET_AUTH_COOKIE_SAMESITE = os.environ.get(
    "MASTER_CABINET_AUTH_COOKIE_SAMESITE", "lax"
)

S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "https://storage.yandexcloud.net")
S3_REGION_NAME = os.environ.get("S3_REGION_NAME", "ru-central1")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "dnd2")
S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID", "YCAJEY0yZHpI1_WLoc92aUmEc")
S3_SECRET_ACCESS_KEY = os.environ.get(
    "S3_SECRET_ACCESS_KEY", "YCOWcVrxhqJaMFyDh0jMs96a-ZSkeNitNq23YQqY"
)

# Список TURN серверов
TURN_SERVERS = [
    # "turn:relay1.expressturn.com:80",
    # "turn:relay1.expressturn.com:443",
    # "turn:relay1.expressturn.com:3478",
    # "turn:relay2.expressturn.com:3478",
    # "turn:relay3.expressturn.com:3478",
    # "turn:relay4.expressturn.com:3478",
    # "turn:relay5.expressturn.com:3478",
    # "turn:relay6.expressturn.com:3478",
    # "turn:relay7.expressturn.com:3478",
    # "turn:relay8.expressturn.com:3478",
    # "turn:relay9.expressturn.com:3478",
    # "turn:relay10.expressturn.com:3478",
    # "turn:relay11.expressturn.com:3478",
    # "turn:relay12.expressturn.com:3478",
    # "turn:relay13.expressturn.com:3478",
    # "turn:relay14.expressturn.com:3478",
    # "turn:relay15.expressturn.com:3478",
    # "turn:relay16.expressturn.com:3478",
    # "turn:relay17.expressturn.com:3478",
    # "turn:relay18.expressturn.com:3478",
    # "turn:relay19.expressturn.com:3478",
    "turn:global.expressturn.com:3478",
]
