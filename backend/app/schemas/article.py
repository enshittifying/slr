"""Article schemas."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ArticleStatus(str, Enum):
    """Article status enum."""

    DRAFT = "draft"
    SP_IN_PROGRESS = "sp_in_progress"
    R1_IN_PROGRESS = "r1_in_progress"
    R2_IN_PROGRESS = "r2_in_progress"
    COMPLETED = "completed"
    PUBLISHED = "published"


class ArticleBase(BaseModel):
    """Base article schema."""

    title: str = Field(..., min_length=1, max_length=1000)
    author_name: str | None = Field(None, max_length=500)
    volume_number: int = Field(..., gt=0)
    issue_number: int = Field(..., gt=0)
    assigned_editor: uuid.UUID | None = None


class ArticleCreate(ArticleBase):
    """Article create schema."""

    pass


class ArticleUpdate(BaseModel):
    """Article update schema."""

    title: str | None = Field(None, min_length=1, max_length=1000)
    author_name: str | None = Field(None, max_length=500)
    status: ArticleStatus | None = None
    assigned_editor: uuid.UUID | None = None


class Article(ArticleBase):
    """Article response schema."""

    id: uuid.UUID
    status: ArticleStatus
    submitted_at: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArticleStats(BaseModel):
    """Article statistics schema."""

    total_citations: int = 0
    sp_completed: int = 0
    r1_completed: int = 0
    r2_completed: int = 0
    requires_manual_review: int = 0
    format_valid: int = 0
    support_valid: int = 0
    quote_valid: int = 0


class ArticleWithStats(Article):
    """Article with statistics."""

    citation_stats: ArticleStats


class PipelineStartRequest(BaseModel):
    """Pipeline start request schema."""

    stages: list[str] = Field(default=["sp", "r1", "r2"], description="Stages to run")


class PipelineStartResponse(BaseModel):
    """Pipeline start response schema."""

    job_id: uuid.UUID
    message: str
    estimated_completion: datetime | None = None
