from __future__ import annotations

import abc
from typing import Protocol

import structlog

from .exceptions import ParserError
from .types import ContentType, ParsedContent


class SupportsParse(Protocol):
    """
    Protocol describing a callable that returns a ParsedContent object.
    """

    async def __call__(self, payload: str) -> ParsedContent:
        ...


class BaseParser(abc.ABC):
    """
    Base class for all parsers working inside the ETL pipeline.
    """

    def __init__(self) -> None:
        self.log = structlog.get_logger(self.__class__.__name__)

    @property
    @abc.abstractmethod
    def content_type(self) -> ContentType:
        """
        Content type produced by the parser.
        """

    @abc.abstractmethod
    def can_handle(self, payload: str) -> bool:
        """
        Lightweight check to understand whether the parser supports the payload.
        """

    @abc.abstractmethod
    async def parse(self, payload: str) -> ParsedContent:
        """
        Fetch and transform the payload into a ParsedContent object.
        """

    async def __call__(self, payload: str) -> ParsedContent:
        if not self.can_handle(payload):
            raise ParserError(f"{self.__class__.__name__} cannot handle provided payload")
        return await self.parse(payload)


