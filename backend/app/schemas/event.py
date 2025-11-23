"""Event schemas."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AttendanceStatus(str, Enum):
    """Attendance status enum."""

    ATTENDING = "attending"
    NOT_ATTENDING = "not_attending"
    MAYBE = "maybe"
    NO_RESPONSE = "no_response"


class EventBase(BaseModel):
    """Base event schema."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    event_date: datetime
    location: str | None = Field(None, max_length=500)


class EventCreate(EventBase):
    """Event create schema."""

    create_attendance_form: bool = False


class EventUpdate(BaseModel):
    """Event update schema."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    event_date: datetime | None = None
    location: str | None = Field(None, max_length=500)


class Event(EventBase):
    """Event response schema."""

    id: uuid.UUID
    google_calendar_event_id: str | None = None
    attendance_form_id: uuid.UUID | None = None
    created_by: uuid.UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceStats(BaseModel):
    """Attendance statistics schema."""

    total_invited: int = 0
    attending: int = 0
    not_attending: int = 0
    maybe: int = 0
    no_response: int = 0


class EventWithStats(Event):
    """Event with attendance statistics."""

    attendee_count: int = 0
    response_rate: float = 0.0


class AttendanceRecordBase(BaseModel):
    """Base attendance record schema."""

    status: AttendanceStatus


class AttendanceRecordCreate(AttendanceRecordBase):
    """Attendance record create schema."""

    user_id: uuid.UUID


class AttendanceRecord(AttendanceRecordBase):
    """Attendance record response schema."""

    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    confirmed_at: datetime

    class Config:
        from_attributes = True
