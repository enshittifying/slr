"""Task schemas."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enum."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskBase(BaseModel):
    """Base task schema."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    due_date: datetime | None = None
    linked_form_id: uuid.UUID | None = None


class TaskCreate(TaskBase):
    """Task create schema."""

    pass


class TaskUpdate(BaseModel):
    """Task update schema."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    due_date: datetime | None = None


class Task(TaskBase):
    """Task response schema."""

    id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskAssignmentBase(BaseModel):
    """Base task assignment schema."""

    status: TaskStatus = TaskStatus.NOT_STARTED
    notes: str | None = None


class TaskAssignmentCreate(BaseModel):
    """Task assignment create schema."""

    user_ids: list[uuid.UUID] = Field(..., min_length=1)


class TaskAssignmentUpdate(BaseModel):
    """Task assignment update schema."""

    status: TaskStatus | None = None
    notes: str | None = None


class TaskAssignment(TaskAssignmentBase):
    """Task assignment response schema."""

    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    assigned_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskWithAssignment(Task):
    """Task with assignment details."""

    assignment: TaskAssignment | None = None
