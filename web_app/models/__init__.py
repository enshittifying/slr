"""SQLAlchemy database models for the SLR system."""

from .base import db
from .user import User
from .task import Task, Assignment
from .form import FormDefinition, FormSubmission
from .attendance import AttendanceLog
from .config import SystemConfig

__all__ = [
    "db",
    "User",
    "Task",
    "Assignment",
    "FormDefinition",
    "FormSubmission",
    "AttendanceLog",
    "SystemConfig",
]
