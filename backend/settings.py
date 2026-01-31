import os

DATABASE_HOST = os.environ.get("SERVICE_DATABASE_HOST", "db")
DATABASE_NAME = os.environ.get("SERVICE_DATABASE_NAME", "dnd")
DATABASE_PORT = int(os.environ.get("SERVICE_DATABASE_PORT", "5432"))

DATABASE_DSN = (
    f"postgresql+asyncpg://dude:dude_password_123@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

DB_CONFIG = {
    "host": DATABASE_HOST,
    "port": DATABASE_PORT,
    "user": "dude",
    "password": "dude_password_123",
    "database": DATABASE_NAME,
}

JANUS_URL = os.environ.get("JANUS_URL", "http://51.250.102.96:8088/janus")

TURN_SERVER_URL = os.environ.get("TURN_SERVER_URL", "turn:free.expressturn.com:3478")
TURN_SERVER_USERNAME = os.environ.get("TURN_SERVER_USERNAME", "000000002084126365")
TURN_SERVER_CREDENTIAL = os.environ.get("TURN_SERVER_CREDENTIAL", "4kbbi1XtfrmjnuxOkgfmU1gF6zw=")

STUN_SERVER_URL = os.environ.get("STUN_SERVER_URL", "stun:stun.l.google.com:19302")
