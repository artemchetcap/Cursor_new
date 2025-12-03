from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ContentType(str, Enum):
    """
    Normalized list of supported content types for the ETL pipeline.
    """

    YOUTUBE = "youtube"
    ARTICLE = "article"
    TEXT = "text"
    FILE = "file"


@dataclass(slots=True)
class ParsedContent:
    """
    Unified representation of a parsed source that can be sent to the LLM layer.
    """

    type: ContentType
    title: str
    body: str
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


