from __future__ import annotations

import os
from typing import Iterable, Mapping

import structlog

log = structlog.get_logger("TokenCounter")


class TokenCounter:
    """
    Lightweight helper around tiktoken with graceful fallbacks.
    Falls back to character-based estimation if tiktoken fails (e.g., SSL issues).
    """

    def __init__(self, model: str) -> None:
        self._encoding = None
        self._use_fallback = False
        
        try:
            import tiktoken
            self._encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            try:
                import tiktoken
                # AICODE-NOTE: gpt-4o-mini is not yet in tiktoken, using cl100k_base fallback.
                self._encoding = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                log.warning("tiktoken fallback failed, using char estimation", error=str(e))
                self._use_fallback = True
        except Exception as e:
            # AICODE-NOTE: SSL errors in corporate networks - fallback to char estimation
            log.warning("tiktoken unavailable, using char estimation", error=str(e))
            self._use_fallback = True

    def count_text(self, text: str | None) -> int:
        if not text:
            return 0
        
        if self._use_fallback or self._encoding is None:
            # Rough estimation: ~4 chars per token for English/mixed text
            return len(text) // 4
        
        return len(self._encoding.encode(text))

    def count_messages(self, messages: Iterable[Mapping[str, str]]) -> int:
        total = 0
        for message in messages:
            total += self.count_text(message.get("role"))
            total += self.count_text(message.get("content"))
        return total


