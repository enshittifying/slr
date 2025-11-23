"""User schemas."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enum."""

    MEMBER_EDITOR = "member_editor"
    SENIOR_EDITOR = "senior_editor"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole


class UserCreate(UserBase):
    """User create schema."""

    pass


class UserUpdate(BaseModel):
    """User update schema."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


class User(UserBase):
    """User response schema."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None
    is_active: bool

    class Config:
        from_attributes = True


class UserWithStats(User):
    """User with statistics."""

    tasks_assigned: int = 0
    tasks_completed: int = 0
    articles_assigned: int = 0
