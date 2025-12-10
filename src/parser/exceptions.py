"""Custom exceptions for EDI parser."""


class EDIParserError(Exception):
    """Base exception for EDI parsing errors."""

    pass


class DelimiterDetectionError(EDIParserError):
    """Exception raised when delimiters cannot be detected from ISA segment."""

    pass


class InvalidISASegmentError(EDIParserError):
    """Exception raised when ISA segment is invalid or malformed."""

    pass


class TokenizationError(EDIParserError):
    """Exception raised during EDI tokenization."""

    pass


class FileSizeExceededError(EDIParserError):
    """Exception raised when EDI file exceeds maximum allowed size."""

    pass


class EmptyFileError(EDIParserError):
    """Exception raised when EDI file is empty."""

    pass


class MissingSegmentError(EDIParserError):
    """Exception raised when a required segment is missing."""

    pass
