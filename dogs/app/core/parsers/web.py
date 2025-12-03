from __future__ import annotations

import asyncio
from typing import Optional
from urllib.parse import urlparse

from newspaper import Article

from .base import BaseParser
from .exceptions import ExtractionError, UnsupportedContentError
from .router import is_http_url, is_youtube_url
from .types import ContentType, ParsedContent


class WebParser(BaseParser):
    """
    Parser that extracts article text via newspaper3k.
    """

    def __init__(self, user_agent: Optional[str] = None) -> None:
        super().__init__()
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        )

    @property
    def content_type(self) -> ContentType:
        return ContentType.ARTICLE

    def can_handle(self, payload: str) -> bool:
        return is_http_url(payload) and not is_youtube_url(payload)

    async def parse(self, payload: str) -> ParsedContent:
        if not self.can_handle(payload):
            raise UnsupportedContentError("URL is not supported by WebParser")

        article = await asyncio.to_thread(self._download_article, payload)
        text = (article.text or "").strip()
        if not text:
            raise ExtractionError("Article text is empty after parsing")

        metadata = {
            "authors": article.authors,
            "top_image": article.top_image,
            "publish_date": article.publish_date.isoformat()
            if article.publish_date
            else None,
        }
        return ParsedContent(
            type=self.content_type,
            title=article.title or self._fallback_title(payload),
            body=text,
            source_url=payload,
            metadata=metadata,
        )

    def _download_article(self, url: str) -> Article:
        article = Article(url, browser_user_agent=self.user_agent)
        article.download()
        # AICODE-TODO: Add custom HTML cleaners if product copy deviates from default heuristics.
        article.parse()
        return article

    def _fallback_title(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or "Web Article"


