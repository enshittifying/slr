"""Common schemas used across the API."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema."""

    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    data: dict[str, Any] | None = None
