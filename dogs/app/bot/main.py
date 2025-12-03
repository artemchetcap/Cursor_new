"""
Bot initialization and dispatcher configuration.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings

# AICODE-NOTE: Используем MemoryStorage для MVP. В продакшене заменить на Redis.
storage = MemoryStorage()

bot = Bot(
    token=settings.TG_TOKEN.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher(storage=storage)


def setup_handlers() -> None:
    """
    Register all routers (handlers) to the dispatcher.
    """
    from app.bot.handlers import admin, message, start

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(message.router)


def setup_middlewares() -> None:
    """
    Register all middlewares to the dispatcher.
    """
    from app.bot.middlewares.user_sync import UserSyncMiddleware

    dp.message.middleware(UserSyncMiddleware())
    dp.callback_query.middleware(UserSyncMiddleware())

