"""Citation schemas."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    """Pipeline status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"


class CitationBase(BaseModel):
    """Base citation schema."""

    footnote_number: int = Field(..., gt=0)
    citation_text: str = Field(..., min_length=1)
    proposition: str | None = None
    source_type: str | None = Field(None, max_length=100)
    source_title: str | None = Field(None, max_length=1000)
    source_author: str | None = Field(None, max_length=500)
    source_url: str | None = Field(None, max_length=2000)


class CitationCreate(CitationBase):
    """Citation create schema."""

    article_id: uuid.UUID


class CitationUpdate(BaseModel):
    """Citation update schema."""

    citation_text: str | None = Field(None, min_length=1)
    proposition: str | None = None
    requires_manual_review: bool | None = None
    manual_review_notes: str | None = None


class Citation(CitationBase):
    """Citation response schema."""

    id: uuid.UUID
    article_id: uuid.UUID

    # Pipeline statuses
    sp_status: PipelineStatus
    sp_pdf_path: str | None = None
    sp_completed_at: datetime | None = None

    r1_status: PipelineStatus
    r1_pdf_path: str | None = None
    r1_metadata: dict[str, Any] | None = None
    r1_completed_at: datetime | None = None

    r2_status: PipelineStatus
    r2_pdf_path: str | None = None
    r2_validation_result: dict[str, Any] | None = None
    r2_completed_at: datetime | None = None

    # Validation results
    format_valid: bool | None = None
    support_valid: bool | None = None
    quote_valid: bool | None = None
    requires_manual_review: bool
    manual_review_notes: str | None = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CitationBulkCreate(BaseModel):
    """Bulk citation create schema."""

    citations: list[CitationCreate] = Field(..., min_length=1)


class CitationUploadResponse(BaseModel):
    """Citation upload response schema."""

    citations_created: int
    errors: list[str] = []
