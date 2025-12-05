from __future__ import annotations

import asyncio
from typing import Optional
from urllib.parse import urlparse

import httpx
from newspaper import Article

from .base import BaseParser
from .exceptions import ExtractionError, UnsupportedContentError
from .router import is_http_url, is_youtube_url
from .types import ContentType, ParsedContent


class WebParser(BaseParser):
    """
    Parser that extracts article text via newspaper3k.
    
    AICODE-NOTE: Используем httpx для загрузки HTML с verify=False,
    чтобы обойти корпоративный SSL-перехват. newspaper3k не поддерживает
    отключение SSL проверки напрямую.
    """

    def __init__(self, user_agent: Optional[str] = None, timeout: float = 30.0) -> None:
        super().__init__()
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        )
        self.timeout = timeout

    @property
    def content_type(self) -> ContentType:
        return ContentType.ARTICLE

    def can_handle(self, payload: str) -> bool:
        return is_http_url(payload) and not is_youtube_url(payload)

    async def parse(self, payload: str) -> ParsedContent:
        if not self.can_handle(payload):
            raise UnsupportedContentError("URL is not supported by WebParser")

        # Загружаем HTML через httpx с отключенной SSL проверкой
        try:
            html = await self._fetch_html(payload)
        except httpx.HTTPStatusError as e:
            raise ExtractionError(f"Failed to fetch article: HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ExtractionError(f"Failed to fetch article: {e}") from e

        article = await asyncio.to_thread(self._parse_html, payload, html)
        
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

    async def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content with SSL verification disabled for corporate proxy.
        """
        async with httpx.AsyncClient(
            verify=False,
            timeout=httpx.Timeout(self.timeout, connect=10.0),
            follow_redirects=True,
        ) as client:
            response = await client.get(
                url,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            return response.text

    def _parse_html(self, url: str, html: str) -> Article:
        """
        Parse pre-fetched HTML with newspaper3k.
        """
        article = Article(url, browser_user_agent=self.user_agent)
        article.download(input_html=html)
        article.parse()
        return article

    def _fallback_title(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or "Web Article"


