"""
Middleware for automatic user synchronization with database.
"""

from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update, User

from app.database.models import User as DBUser

log = structlog.get_logger("UserSyncMiddleware")


class UserSyncMiddleware(BaseMiddleware):
    """
    Middleware that creates or updates User in DB on every incoming update.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = None

        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            db_user = await self._sync_user(user)
            data["db_user"] = db_user

        return await handler(event, data)

    async def _sync_user(self, tg_user: User) -> DBUser:
        """
        Create or update user in database.
        """
        # AICODE-NOTE: Используем update_or_create для атомарной операции.
        # Поля username и full_name могут меняться, поэтому обновляем их.
        db_user, created = await DBUser.update_or_create(
            telegram_id=tg_user.id,
            defaults={
                "username": tg_user.username,
                "full_name": tg_user.full_name,
            },
        )
        if created:
            log.info("New user created", telegram_id=tg_user.id, username=tg_user.username)
        return db_user

