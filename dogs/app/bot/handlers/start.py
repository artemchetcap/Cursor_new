"""
Handler for /start and /help commands.
"""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.database.models import User as DBUser

router = Router(name="start")

WELCOME_MESSAGE = """
👋 <b>Привет!</b>

Я — <b>Smart Summarizer Bot</b> 🧠

Моя миссия — <b>сэкономить твое время</b>. Отправь мне:
• 🎬 Ссылку на YouTube-видео
• 📰 Ссылку на статью
• 📝 Любой текст

И я за секунды дам тебе <b>выжимку</b> с ключевыми идеями и практическими действиями!

<i>Больше никаких "посмотрю потом" — узнай суть сейчас.</i>
"""

HELP_MESSAGE = """
📖 <b>Как пользоваться ботом:</b>

1️⃣ <b>YouTube</b> — отправь ссылку, и я извлеку субтитры и сделаю саммари.
2️⃣ <b>Статьи</b> — отправь URL любой статьи, я прочитаю её за тебя.
3️⃣ <b>Текст</b> — просто пришли текст, и получишь структурированную выжимку.

<b>Что ты получишь:</b>
🎯 TL;DR — суть в двух предложениях
🔑 Key Insights — главные тезисы
🛠 Action Items — что можно применить
🏷 Tags — автоматические хештеги
⏱ Reading Time — сколько времени сэкономлено

<i>⚡️ Fast read with @{bot_username}</i>
"""


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: DBUser) -> None:
    """
    Handle /start command with onboarding message.
    """
    await message.answer(WELCOME_MESSAGE)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Handle /help command.
    """
    bot_info = await message.bot.get_me()
    help_text = HELP_MESSAGE.format(bot_username=bot_info.username or "SummarizerBot")
    await message.answer(help_text)

