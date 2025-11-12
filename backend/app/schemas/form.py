"""Form schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FormFieldBase(BaseModel):
    """Base form field schema."""

    field_type: str = Field(..., max_length=50)
    label: str = Field(..., min_length=1, max_length=500)
    field_name: str = Field(..., min_length=1, max_length=100)
    is_required: bool = False
    options: dict[str, Any] | None = None
    validation_rules: dict[str, Any] | None = None
    display_order: int = Field(..., ge=0)


class FormFieldCreate(FormFieldBase):
    """Form field create schema."""

    pass


class FormField(FormFieldBase):
    """Form field response schema."""

    id: uuid.UUID
    form_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class FormBase(BaseModel):
    """Base form schema."""

    name: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    is_active: bool = True


class FormCreate(FormBase):
    """Form create schema."""

    fields: list[FormFieldCreate] = []


class FormUpdate(BaseModel):
    """Form update schema."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    is_active: bool | None = None


class Form(FormBase):
    """Form response schema."""

    id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    field_count: int = 0

    class Config:
        from_attributes = True


class FormWithFields(Form):
    """Form with fields."""

    fields: list[FormField]


class FormSubmissionBase(BaseModel):
    """Base form submission schema."""

    submission_data: dict[str, Any] = Field(..., description="Form field values")


class FormSubmissionCreate(FormSubmissionBase):
    """Form submission create schema."""

    pass


class FormSubmission(FormSubmissionBase):
    """Form submission response schema."""

    id: uuid.UUID
    form_id: uuid.UUID
    submitted_by: uuid.UUID
    submitted_at: datetime

    class Config:
        from_attributes = True
