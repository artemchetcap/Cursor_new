from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.core.parsers.types import ContentType


@dataclass(slots=True)
class SummaryPayload:
    """
    Request data passed to the LLM summarizer.
    """

    content: str
    title: str
    content_type: ContentType
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TokenUsage:
    prompt: int
    completion: int


@dataclass(slots=True)
class SummaryResult:
    text: str
    tokens: TokenUsage
    model: str


