from __future__ import annotations

import asyncio
import re
from typing import Optional, Sequence, Tuple
from urllib.request import urlopen

import yt_dlp

from .base import BaseParser
from .exceptions import ExtractionError, UnsupportedContentError
from .router import is_youtube_url
from .types import ContentType, ParsedContent

_TIMESTAMP_PATTERN = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3}")


class YouTubeParser(BaseParser):
    """
    Parser that fetches subtitles with yt-dlp and converts them into text.

    AICODE-NOTE: YouTube парсинг временно не работает из-за ограничений yt-dlp/YouTube.
    Бот будет возвращать ошибку при попытке обработать YouTube ссылки.
    Статус: ожидаем обновление yt-dlp или альтернативное решение.
    """

    def __init__(
        self,
        preferred_languages: Optional[Sequence[str]] = None,
        subtitle_timeout: int = 10,
    ) -> None:
        super().__init__()
        self.preferred_languages = [
            lang.lower() for lang in (preferred_languages or ("ru", "en"))
        ]
        self.subtitle_timeout = subtitle_timeout

    @property
    def content_type(self) -> ContentType:
        return ContentType.YOUTUBE

    def can_handle(self, payload: str) -> bool:
        return is_youtube_url(payload)

    async def parse(self, payload: str) -> ParsedContent:
        if not self.can_handle(payload):
            raise UnsupportedContentError("Provided URL is not a YouTube link")

        info = await asyncio.to_thread(self._extract_video_info, payload)
        subtitle_url, subtitle_lang = self._resolve_subtitle_url(info)
        if not subtitle_url:
            raise ExtractionError("Subtitles are not available for this video")

        raw_vtt = await asyncio.to_thread(self._download_subtitle, subtitle_url)
        body = self._vtt_to_text(raw_vtt)
        if not body:
            raise ExtractionError("Parsed subtitle text is empty")

        metadata = {
            "language": subtitle_lang,
            "duration": info.get("duration"),
            "channel": info.get("uploader"),
        }
        return ParsedContent(
            type=self.content_type,
            title=info.get("title") or "YouTube Video",
            body=body,
            source_url=payload,
            metadata=metadata,
        )

    def _extract_video_info(self, url: str) -> dict:
        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitlesformat": "vtt",
            "subtitleslangs": self.preferred_languages,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _resolve_subtitle_url(self, info: dict) -> Tuple[Optional[str], Optional[str]]:
        candidates = [
            self._select_track(info.get("subtitles") or {}),
            self._select_track(info.get("automatic_captions") or {}),
        ]
        for track_url, language in candidates:
            if track_url:
                return track_url, language
        return None, None

    def _select_track(self, tracks: dict) -> Tuple[Optional[str], Optional[str]]:
        for lang in self.preferred_languages:
            lang_variants = {lang, lang.split("-")[0]}
            for variant in lang_variants:
                if variant in tracks and tracks[variant]:
                    return tracks[variant][0].get("url"), variant
        return None, None

    def _download_subtitle(self, url: str) -> str:
        with urlopen(url, timeout=self.subtitle_timeout) as response:  # nosec B310
            return response.read().decode("utf-8", errors="ignore")

    def _vtt_to_text(self, subtitle: str) -> str:
        """
        Simplistic VTT to text converter that strips timestamps and cue ids.
        """

        lines = []
        for row in subtitle.splitlines():
            normalized = row.strip()
            if (
                not normalized
                or normalized.upper() == "WEBVTT"
                or "-->" in normalized
                or normalized.isdigit()
                or _TIMESTAMP_PATTERN.match(normalized)
            ):
                continue
            lines.append(normalized)
        # AICODE-NOTE: Joining with space keeps inline punctuation intact while avoiding double newlines.
        return " ".join(lines).strip()


