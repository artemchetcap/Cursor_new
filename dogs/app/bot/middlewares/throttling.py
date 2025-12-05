"""
Rate limiting middleware to protect from spam.
"""

import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.core.config import settings

log = structlog.get_logger("ThrottlingMiddleware")

# AICODE-NOTE: Используем in-memory хранилище для MVP.
# В продакшене заменить на Redis для персистентности между перезапусками.


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware that limits the number of requests per user within a time window.
    
    Admins are exempt from rate limiting.
    """

    def __init__(
        self,
        max_requests: int | None = None,
        period_seconds: int | None = None,
    ) -> None:
        self.max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        self.period_seconds = period_seconds or settings.RATE_LIMIT_PERIOD
        # user_id -> list of timestamps
        self._requests: Dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        user_id = user.id

        # Админы не ограничиваются
        if user_id in settings.admin_ids_list:
            return await handler(event, data)

        # Проверяем rate limit
        if self._is_rate_limited(user_id):
            log.warning(
                "User rate limited",
                user_id=user_id,
                username=user.username,
            )
            await event.answer(
                "⏳ <b>Слишком много запросов!</b>\n\n"
                f"Подождите немного. Лимит: {self.max_requests} запросов "
                f"за {self.period_seconds} секунд.",
            )
            return None

        # Записываем запрос
        self._record_request(user_id)
        return await handler(event, data)

    def _is_rate_limited(self, user_id: int) -> bool:
        """Check if user has exceeded the rate limit."""
        now = time.time()
        cutoff = now - self.period_seconds

        # Очищаем старые записи
        self._requests[user_id] = [
            ts for ts in self._requests[user_id] if ts > cutoff
        ]

        return len(self._requests[user_id]) >= self.max_requests

    def _record_request(self, user_id: int) -> None:
        """Record a new request for the user."""
        self._requests[user_id].append(time.time())

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get rate limit stats for a user (for debugging)."""
        now = time.time()
        cutoff = now - self.period_seconds
        recent = [ts for ts in self._requests[user_id] if ts > cutoff]
        return {
            "requests_in_window": len(recent),
            "max_requests": self.max_requests,
            "remaining": max(0, self.max_requests - len(recent)),
        }

