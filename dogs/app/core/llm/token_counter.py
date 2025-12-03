from __future__ import annotations

from typing import Iterable, Mapping

import tiktoken


class TokenCounter:
    """
    Lightweight helper around tiktoken with graceful fallbacks.
    """

    def __init__(self, model: str) -> None:
        try:
            self._encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # AICODE-NOTE: gpt-4o-mini is not yet in tiktoken, using cl100k_base fallback.
            self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_text(self, text: str | None) -> int:
        if not text:
            return 0
        return len(self._encoding.encode(text))

    def count_messages(self, messages: Iterable[Mapping[str, str]]) -> int:
        total = 0
        for message in messages:
            total += self.count_text(message.get("role"))
            total += self.count_text(message.get("content"))
        return total


