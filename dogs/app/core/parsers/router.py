from __future__ import annotations

import re
from typing import Sequence
from urllib.parse import urlparse

from .base import BaseParser
from .exceptions import UnsupportedContentError
from .types import ContentType

YOUTUBE_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "music.youtube.com",
}

_URL_REGEX = re.compile(r"https?://", re.IGNORECASE)


def is_probably_url(payload: str) -> bool:
    if not payload:
        return False
    return bool(_URL_REGEX.match(payload.strip()))


def is_youtube_url(payload: str) -> bool:
    try:
        parsed = urlparse(payload.strip())
    except ValueError:
        return False
    if not parsed.netloc:
        return False
    return parsed.netloc.lower() in YOUTUBE_DOMAINS


def is_http_url(payload: str) -> bool:
    try:
        parsed = urlparse(payload.strip())
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    return bool(parsed.netloc)


def detect_content_type(payload: str) -> ContentType:
    """
    Naive router that classifies the incoming payload for downstream services.
    """

    normalized = (payload or "").strip()
    if not normalized:
        raise ValueError("Empty payload cannot be routed")

    if is_youtube_url(normalized):
        return ContentType.YOUTUBE
    if is_http_url(normalized):
        return ContentType.ARTICLE
    return ContentType.TEXT


def select_parser(payload: str, parsers: Sequence[BaseParser]) -> BaseParser:
    """
    Select the most appropriate parser for the payload.
    """

    target_type = detect_content_type(payload)
    for parser in parsers:
        if parser.content_type == target_type and parser.can_handle(payload):
            return parser
    raise UnsupportedContentError(f"No parser available for {target_type.value}")


