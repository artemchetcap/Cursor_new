"""
Entry point for Smart Summarizer Bot.
"""

import asyncio
import signal
import sys
from typing import Optional

import structlog

from app.bot.main import bot, dp, setup_handlers, setup_middlewares
from app.core.logger import setup_logging
from app.database.db import close_db, init_db

log: Optional[structlog.stdlib.BoundLogger] = None


async def on_startup() -> None:
    """
    Actions to perform on bot startup.
    """
    log.info("Initializing database...")
    await init_db()
    log.info("Database initialized")

    log.info("Setting up handlers and middlewares...")
    setup_handlers()
    setup_middlewares()
    log.info("Handlers and middlewares configured")

    bot_info = await bot.get_me()
    log.info(
        "Bot started",
        username=bot_info.username,
        bot_id=bot_info.id,
    )


async def on_shutdown() -> None:
    """
    Actions to perform on bot shutdown.
    """
    log.info("Shutting down...")
    await close_db()
    await bot.session.close()
    log.info("Shutdown complete")


async def main() -> None:
    """
    Main entry point.
    """
    global log

    # Setup logging first
    setup_logging()
    log = structlog.get_logger("main")

    log.info("Starting Smart Summarizer Bot...")

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    # AICODE-NOTE: Используем polling для dev-среды. В продакшене рекомендуется webhook.
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    except asyncio.CancelledError:
        log.info("Bot polling cancelled")


def handle_signal(sig: signal.Signals) -> None:
    """
    Handle termination signals for graceful shutdown.
    """
    if log:
        log.info("Received signal", signal=sig.name)
    # Let asyncio handle the cancellation
    raise KeyboardInterrupt


if __name__ == "__main__":
    # Setup signal handlers for graceful shutdown
    if sys.platform != "win32":
        loop = asyncio.new_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))
        asyncio.set_event_loop(loop)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Graceful exit
