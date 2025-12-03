"""
Admin handlers (restricted to ADMIN_IDS).
"""

from datetime import datetime, timedelta
from typing import Any

import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from tortoise.functions import Count, Sum

from app.core.config import settings
from app.database.models import SummaryRequest, User

router = Router(name="admin")
log = structlog.get_logger("AdminHandler")


class AdminFilter:
    """
    Filter that allows only users from ADMIN_IDS.
    """

    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        return message.from_user.id in settings.admin_ids_list


admin_filter = AdminFilter()


async def _get_stats(since: datetime) -> dict[str, Any]:
    """
    Collect statistics from database since given datetime.
    """
    new_users = await User.filter(created_at__gte=since).count()

    requests = await SummaryRequest.filter(created_at__gte=since).all()
    total_requests = len(requests)
    successful_requests = len([r for r in requests if r.status == "success"])
    failed_requests = len([r for r in requests if r.status == "error"])
    total_tokens = sum(r.tokens_used for r in requests)

    return {
        "new_users": new_users,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "total_tokens": total_tokens,
    }


def _format_stats_message(
    stats_24h: dict[str, Any], 
    stats_7d: dict[str, Any], 
    total_users: int, 
    total_requests: int
) -> str:
    """
    Format statistics into a readable message.
    """
    return f"""
📊 <b>Статистика бота</b>

<b>За последние 24 часа:</b>
👤 Новых пользователей: <code>{stats_24h['new_users']}</code>
📩 Всего запросов: <code>{stats_24h['total_requests']}</code>
✅ Успешных: <code>{stats_24h['successful_requests']}</code>
❌ С ошибками: <code>{stats_24h['failed_requests']}</code>
🔢 Токенов использовано: <code>{stats_24h['total_tokens']:,}</code>

<b>За последние 7 дней:</b>
👤 Новых пользователей: <code>{stats_7d['new_users']}</code>
📩 Всего запросов: <code>{stats_7d['total_requests']}</code>
✅ Успешных: <code>{stats_7d['successful_requests']}</code>
❌ С ошибками: <code>{stats_7d['failed_requests']}</code>
🔢 Токенов использовано: <code>{stats_7d['total_tokens']:,}</code>

<b>Всего в системе:</b>
👥 Пользователей: <code>{total_users}</code>
📝 Запросов: <code>{total_requests}</code>
""".strip()


@router.message(Command("stats"), admin_filter)
async def cmd_stats(message: Message) -> None:
    """
    Handle /stats command for admins only.
    Shows statistics for last 24h and 7 days.
    """
    log.info("Admin stats requested", admin_id=message.from_user.id)

    now = datetime.utcnow()
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    stats_24h = await _get_stats(since_24h)
    stats_7d = await _get_stats(since_7d)

    # Get total counts
    total_users = await User.all().count()
    total_requests = await SummaryRequest.all().count()

    response = f"""
📊 <b>Статистика бота</b>

<b>За последние 24 часа:</b>
👤 Новых пользователей: <code>{stats_24h['new_users']}</code>
📩 Всего запросов: <code>{stats_24h['total_requests']}</code>
✅ Успешных: <code>{stats_24h['successful_requests']}</code>
❌ С ошибками: <code>{stats_24h['failed_requests']}</code>
🔢 Токенов использовано: <code>{stats_24h['total_tokens']:,}</code>

<b>За последние 7 дней:</b>
👤 Новых пользователей: <code>{stats_7d['new_users']}</code>
📩 Всего запросов: <code>{stats_7d['total_requests']}</code>
✅ Успешных: <code>{stats_7d['successful_requests']}</code>
❌ С ошибками: <code>{stats_7d['failed_requests']}</code>
🔢 Токенов использовано: <code>{stats_7d['total_tokens']:,}</code>

<b>Всего в системе:</b>
👥 Пользователей: <code>{total_users}</code>
📝 Запросов: <code>{total_requests}</code>
"""

    await message.answer(response.strip())

