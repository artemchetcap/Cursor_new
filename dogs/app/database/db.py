import os

from tortoise import Tortoise

# AICODE-NOTE: Используем переменную окружения для Docker-совместимости.
# В контейнере путь будет sqlite://./db/db.sqlite3 для persistence.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://db.sqlite3")

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.database.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}

async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    # await Tortoise.generate_schemas() # We use migrations instead

async def close_db():
    await Tortoise.close_connections()

