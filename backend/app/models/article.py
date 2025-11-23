"""Article model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.citation import Citation
    from app.models.user import User


class Article(Base):
    """Article model."""

    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    author_name: Mapped[str | None] = mapped_column(String(500))
    volume_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(
            "draft",
            "sp_in_progress",
            "r1_in_progress",
            "r2_in_progress",
            "completed",
            "published",
            name="article_status",
            create_type=False,
        ),
        default="draft",
        nullable=False,
        index=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_editor: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
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
    citations: Mapped[list["Citation"]] = relationship(
        "Citation", back_populates="article", cascade="all, delete-orphan"
    )
    assigned_editor_rel: Mapped["User"] = relationship("User", back_populates="assigned_articles")

    def __repr__(self) -> str:
        return f"<Article {self.title}>"
