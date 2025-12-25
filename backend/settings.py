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
