class ParserError(RuntimeError):
    """Base exception for parser related issues."""


class UnsupportedContentError(ParserError):
    """Raised when a parser cannot process a given payload."""


class ExtractionError(ParserError):
    """Raised when the parser fails to extract text from the source."""


