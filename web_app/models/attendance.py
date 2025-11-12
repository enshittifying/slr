"""Attendance tracking model."""

from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from .base import db, BaseModel


class AttendanceLog(BaseModel):
    """
    Attendance Log model for tracking member attendance at events.
    """

    __tablename__ = "attendance_log"

    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_name = db.Column(db.String(500), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    logged_at = db.Column(db.DateTime, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="attendance_logs")

    __table_args__ = (
        CheckConstraint(
            "status IN ('attending', 'not_attending', 'maybe')",
            name="valid_attendance_status",
        ),
        db.Index("idx_attendance_user_event", "user_id", "event_date"),
    )

    def __repr__(self):
        return f"<AttendanceLog user={self.user_id} event={self.event_name} status={self.status}>"

    def to_dict(self):
        """Convert attendance log to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "event_name": self.event_name,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "status": self.status,
            "logged_at": self.logged_at.isoformat() if self.logged_at else None,
            "user": self.user.to_dict() if self.user else None,
        }
