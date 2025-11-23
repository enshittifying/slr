"""Form definition and submission models."""

from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from .base import db, BaseModel


class FormDefinition(BaseModel):
    """
    Form Definition model for storing metadata about dynamically generated Google Forms.
    """

    __tablename__ = "form_definitions"

    form_name = db.Column(db.String(255), nullable=False, index=True)
    google_form_id = db.Column(db.String(255))  # Generated Google Form ID
    item_id = db.Column(db.Integer)  # Question item ID within the form
    question_title = db.Column(db.Text)
    item_type = db.Column(db.String(50))
    options = db.Column(db.Text)  # JSON array stored as text for choices

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('text', 'multiple_choice', 'checkbox', 'date', 'email', 'paragraph')",
            name="valid_item_type",
        ),
    )

    def __repr__(self):
        return f"<FormDefinition {self.form_name} - {self.question_title}>"

    def to_dict(self):
        """Convert form definition to dictionary."""
        return {
            "id": str(self.id),
            "form_name": self.form_name,
            "google_form_id": self.google_form_id,
            "item_id": self.item_id,
            "question_title": self.question_title,
            "item_type": self.item_type,
            "options": self.options,
        }


class FormSubmission(BaseModel):
    """
    Form Submission model for logging all form responses.
    """

    __tablename__ = "form_submissions"

    form_id = db.Column(db.String(255), nullable=False, index=True)  # Google Form ID
    user_email = db.Column(db.String(255), nullable=False, index=True)
    responses = db.Column(JSONB, nullable=False)  # Store all responses as JSONB
    submitted_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<FormSubmission form={self.form_id} user={self.user_email}>"

    def to_dict(self):
        """Convert form submission to dictionary."""
        return {
            "id": str(self.id),
            "form_id": self.form_id,
            "user_email": self.user_email,
            "responses": self.responses,
            "submitted_at": (
                self.submitted_at.isoformat() if self.submitted_at else None
            ),
        }
