"""
Handler for processing user messages (links, text).
"""

from __future__ import annotations

from typing import Optional

import structlog
from aiogram import F, Router
from aiogram.types import Message, ReactionTypeEmoji

from app.core.llm.service import build_llm_service
from app.core.llm.types import SummaryPayload
from app.core.parsers.base import BaseParser
from app.core.parsers.exceptions import ExtractionError, ParserError, UnsupportedContentError
from app.core.parsers.router import detect_content_type, is_probably_url, select_parser
from app.core.parsers.types import ContentType, ParsedContent
from app.core.parsers.web import WebParser
from app.core.parsers.youtube import YouTubeParser
from app.database.models import SummaryRequest, User as DBUser

router = Router(name="message")
log = structlog.get_logger("MessageHandler")

# AICODE-NOTE: Парсеры инициализируются один раз на старте модуля.
# В продакшене можно вынести в DI-контейнер.
PARSERS: list[BaseParser] = [
    YouTubeParser(),
    WebParser(),
]

FOOTER_TEMPLATE = "\n\n<i>⚡️ Fast read with @{bot_username}</i>"

ERROR_MESSAGES = {
    "unsupported": "❌ <b>Не удалось обработать контент</b>\n\nЭтот тип контента пока не поддерживается.",
    "extraction": "❌ <b>Не удалось извлечь контент</b>\n\n{details}",
    "parsing": "❌ <b>Ошибка при обработке</b>\n\nПопробуйте ещё раз или отправьте другую ссылку.",
    "llm": "❌ <b>Ошибка генерации саммари</b>\n\nСервис временно недоступен. Попробуйте позже.",
    "empty": "🤔 <b>Пустое сообщение</b>\n\nОтправьте мне ссылку или текст для анализа.",
}


async def _set_reaction(message: Message, emoji: str) -> None:
    """
    Safely set reaction on message.
    """
    try:
        await message.react([ReactionTypeEmoji(emoji=emoji)])
    except Exception:
        # AICODE-NOTE: Реакции могут быть недоступны в некоторых чатах.
        pass


async def _send_typing(message: Message) -> None:
    """
    Send typing action to show bot is processing.
    """
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
    except Exception:
        pass


def _extract_url_from_message(message: Message) -> Optional[str]:
    """
    Extract URL from message text or entities.
    """
    text = message.text or message.caption or ""

    # Check entities for URLs
    entities = message.entities or message.caption_entities or []
    for entity in entities:
        if entity.type in ("url", "text_link"):
            if entity.type == "text_link" and entity.url:
                return entity.url
            elif entity.type == "url":
                return text[entity.offset : entity.offset + entity.length]

    # Fallback: check if whole text is a URL
    if is_probably_url(text):
        return text.strip()

    return None


def _extract_forwarded_text(message: Message) -> Optional[str]:
    """
    Extract text from forwarded message.
    """
    if message.forward_date:
        return message.text or message.caption
    return None


async def _parse_content(payload: str, content_type: ContentType) -> ParsedContent:
    """
    Parse content using appropriate parser.
    """
    if content_type == ContentType.TEXT:
        # Direct text doesn't need parsing
        return ParsedContent(
            type=ContentType.TEXT,
            title="Текст от пользователя",
            body=payload,
        )

    parser = select_parser(payload, PARSERS)
    return await parser.parse(payload)


async def _create_summary_request(
    db_user: DBUser,
    content_type: ContentType,
    source_url: Optional[str] = None,
) -> SummaryRequest:
    """
    Create a new SummaryRequest record with 'processing' status.
    """
    return await SummaryRequest.create(
        user=db_user,
        content_type=content_type.value,
        source_url=source_url,
        status="processing",
    )


async def _update_summary_request(
    request: SummaryRequest,
    status: str,
    tokens_used: int = 0,
    error_message: Optional[str] = None,
) -> None:
    """
    Update SummaryRequest with final status.
    """
    request.status = status
    request.tokens_used = tokens_used
    if error_message:
        request.error_message = error_message
    await request.save()


@router.message(F.text | F.caption)
async def handle_message(message: Message, db_user: DBUser) -> None:
    """
    Main handler for processing user messages with links or text.
    """
    text = message.text or message.caption or ""

    if not text.strip():
        await message.answer(ERROR_MESSAGES["empty"])
        return

    # Set acknowledgment reaction
    await _set_reaction(message, "👀")
    await _send_typing(message)

    # Determine content type and extract payload
    url = _extract_url_from_message(message)
    forwarded_text = _extract_forwarded_text(message)

    if url:
        payload = url
        try:
            content_type = detect_content_type(payload)
        except ValueError:
            content_type = ContentType.TEXT
    elif forwarded_text:
        payload = forwarded_text
        content_type = ContentType.TEXT
    else:
        payload = text.strip()
        content_type = ContentType.TEXT

    log.info(
        "Processing message",
        telegram_id=db_user.telegram_id,
        content_type=content_type.value,
        has_url=bool(url),
    )

    # Create SummaryRequest for analytics
    summary_request = await _create_summary_request(
        db_user=db_user,
        content_type=content_type,
        source_url=url,
    )

    try:
        # Parse content
        parsed = await _parse_content(payload, content_type)

        # Send another typing indicator before LLM call
        await _send_typing(message)

        # Build LLM service and summarize
        llm_service = build_llm_service()
        summary_payload = SummaryPayload(
            content=parsed.body,
            title=parsed.title,
            content_type=parsed.type,
            source_url=parsed.source_url,
            metadata=parsed.metadata,
        )
        result = await llm_service.summarize(summary_payload)

        # Update request with success
        total_tokens = result.tokens.prompt + result.tokens.completion
        await _update_summary_request(summary_request, "success", tokens_used=total_tokens)

        # Build response with footer
        bot_info = await message.bot.get_me()
        footer = FOOTER_TEMPLATE.format(bot_username=bot_info.username or "SummarizerBot")
        response = result.text + footer

        await message.answer(response)
        await _set_reaction(message, "✅")

        log.info(
            "Summary sent",
            telegram_id=db_user.telegram_id,
            tokens_used=total_tokens,
            model=result.model,
        )

    except UnsupportedContentError as e:
        await _update_summary_request(summary_request, "error", error_message=str(e))
        await message.answer(ERROR_MESSAGES["unsupported"])
        log.warning("Unsupported content", error=str(e))

    except ExtractionError as e:
        await _update_summary_request(summary_request, "error", error_message=str(e))
        error_text = ERROR_MESSAGES["extraction"].format(details=str(e))
        await message.answer(error_text)
        log.warning("Extraction error", error=str(e))

    except ParserError as e:
        await _update_summary_request(summary_request, "error", error_message=str(e))
        await message.answer(ERROR_MESSAGES["parsing"])
        log.error("Parser error", error=str(e))

    except Exception as e:
        await _update_summary_request(summary_request, "error", error_message=str(e))
        await message.answer(ERROR_MESSAGES["llm"])
        log.exception("Unexpected error during message processing", error=str(e))

