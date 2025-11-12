"""Citation model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.article import Article


class Citation(Base):
    """Citation model."""

    __tablename__ = "citations"
    __table_args__ = (
        UniqueConstraint("article_id", "footnote_number", name="uq_article_footnote"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    footnote_number: Mapped[int] = mapped_column(Integer, nullable=False)
    citation_text: Mapped[str] = mapped_column(Text, nullable=False)
    proposition: Mapped[str | None] = mapped_column(Text)

    # Source information
    source_type: Mapped[str | None] = mapped_column(String(100))
    source_title: Mapped[str | None] = mapped_column(String(1000))
    source_author: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(String(2000))

    # Stage 1: Sourcepull status
    sp_status: Mapped[str] = mapped_column(
        SQLEnum(
            "pending",
            "in_progress",
            "completed",
            "failed",
            "manual_required",
            name="pipeline_status",
            create_type=False,
        ),
        default="pending",
        nullable=False,
        index=True,
    )
    sp_pdf_path: Mapped[str | None] = mapped_column(String(1000))
    sp_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Stage 2: R1 (Preparation) status
    r1_status: Mapped[str] = mapped_column(
        SQLEnum(
            "pending",
            "in_progress",
            "completed",
            "failed",
            "manual_required",
            name="pipeline_status",
            create_type=False,
        ),
        default="pending",
        nullable=False,
        index=True,
    )
    r1_pdf_path: Mapped[str | None] = mapped_column(String(1000))
    r1_metadata: Mapped[dict | None] = mapped_column(JSONB)
    r1_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Stage 3: R2 (Validation) status
    r2_status: Mapped[str] = mapped_column(
        SQLEnum(
            "pending",
            "in_progress",
            "completed",
            "failed",
            "manual_required",
            name="pipeline_status",
            create_type=False,
        ),
        default="pending",
        nullable=False,
        index=True,
    )
    r2_pdf_path: Mapped[str | None] = mapped_column(String(1000))
    r2_validation_result: Mapped[dict | None] = mapped_column(JSONB)
    r2_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Validation results
    format_valid: Mapped[bool | None] = mapped_column(Boolean)
    support_valid: Mapped[bool | None] = mapped_column(Boolean)
    quote_valid: Mapped[bool | None] = mapped_column(Boolean)
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    manual_review_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="citations")

    def __repr__(self) -> str:
        return f"<Citation {self.article_id}:{self.footnote_number}>"
