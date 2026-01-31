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

TURN_SERVER_USERNAME = os.environ.get("TURN_SERVER_USERNAME", "000000002084126365")
TURN_SERVER_CREDENTIAL = os.environ.get("TURN_SERVER_CREDENTIAL", "4kbbi1XtfrmjnuxOkgfmU1gF6zw=")

STUN_SERVER_URL = os.environ.get("STUN_SERVER_URL", "stun:stun.l.google.com:19302")

# Список TURN серверов
TURN_SERVERS = [
    "turn:relay1.expressturn.com:80",
    "turn:relay1.expressturn.com:443",
    "turn:relay1.expressturn.com:3478",
    "turn:relay2.expressturn.com:3478",
    "turn:relay3.expressturn.com:3478",
    "turn:relay4.expressturn.com:3478",
    "turn:relay5.expressturn.com:3478",
    "turn:relay6.expressturn.com:3478",
    "turn:relay7.expressturn.com:3478",
    "turn:relay8.expressturn.com:3478",
    "turn:relay9.expressturn.com:3478",
    "turn:relay10.expressturn.com:3478",
    "turn:relay11.expressturn.com:3478",
    "turn:relay12.expressturn.com:3478",
    "turn:relay13.expressturn.com:3478",
    "turn:relay14.expressturn.com:3478",
    "turn:relay15.expressturn.com:3478",
    "turn:relay16.expressturn.com:3478",
    "turn:relay17.expressturn.com:3478",
    "turn:relay18.expressturn.com:3478",
    "turn:relay19.expressturn.com:3478",
    "turn:global.expressturn.com:3478",
]
