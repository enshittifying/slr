"""Custom exceptions for the SLR system."""


class SLRException(Exception):
    """Base exception for all SLR-related errors."""

    pass


class SpreadsheetError(SLRException):
    """Exception raised for errors in spreadsheet operations."""

    pass


class PDFProcessingError(SLRException):
    """Exception raised for errors in PDF processing."""

    pass


class CitationParsingError(SLRException):
    """Exception raised for errors in citation parsing."""

    pass


class ValidationError(SLRException):
    """Exception raised for validation errors."""

    pass


class AuthenticationError(SLRException):
    """Exception raised for authentication errors."""

    pass


class RateLimitError(SLRException):
    """Exception raised when rate limits are exceeded."""

    pass


class SourceNotFoundError(SLRException):
    """Exception raised when a source cannot be found."""

    pass
