"""User model for Member Editors."""

from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from .base import db, BaseModel


class User(BaseModel, UserMixin):
    """
    User model representing Member Editors, Senior Editors, and Admins.
    """

    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(50),
        nullable=False,
        default="member_editor",
    )

    # Relationships
    assignments = db.relationship(
        "Assignment", back_populates="user", cascade="all, delete-orphan"
    )
    attendance_logs = db.relationship(
        "AttendanceLog", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('member_editor', 'senior_editor', 'admin')",
            name="valid_role",
        ),
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return self.role == role

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == "admin"

    def is_senior_editor(self) -> bool:
        """Check if user is a senior editor or admin."""
        return self.role in ("senior_editor", "admin")

    def to_dict(self):
        """Convert user to dictionary (excluding sensitive fields)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
