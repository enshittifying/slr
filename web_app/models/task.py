"""Task and Assignment models."""

from datetime import datetime
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from .base import db, BaseModel


class Task(BaseModel):
    """
    Task model representing work items that can be assigned to users.
    """

    __tablename__ = "tasks"

    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    linked_form_id = db.Column(db.String(255))  # Google Form ID if applicable

    # Relationships
    assignments = db.relationship(
        "Assignment", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Task {self.title}>"

    def to_dict(self):
        """Convert task to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "linked_form_id": self.linked_form_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Assignment(BaseModel):
    """
    Assignment model representing the many-to-many relationship between users and tasks.
    Tracks the status of a task assigned to a specific user.
    """

    __tablename__ = "assignments"

    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    task_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    status = db.Column(db.String(50), nullable=False, default="not_started", index=True)
    date_completed = db.Column(db.DateTime)

    # Relationships
    user = db.relationship("User", back_populates="assignments")
    task = db.relationship("Task", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="unique_user_task_assignment"),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="valid_status",
        ),
    )

    def __repr__(self):
        return f"<Assignment user={self.user_id} task={self.task_id} status={self.status}>"

    def mark_completed(self):
        """Mark the assignment as completed."""
        self.status = "completed"
        self.date_completed = datetime.utcnow()

    def to_dict(self):
        """Convert assignment to dictionary with related data."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "task_id": str(self.task_id),
            "status": self.status,
            "date_completed": (
                self.date_completed.isoformat() if self.date_completed else None
            ),
            "task": self.task.to_dict() if self.task else None,
            "user": self.user.to_dict() if self.user else None,
        }
