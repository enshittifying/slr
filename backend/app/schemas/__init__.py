"""Pydantic schemas for API requests and responses."""

from app.schemas.article import (
    Article,
    ArticleCreate,
    ArticleStats,
    ArticleUpdate,
    ArticleWithStats,
)
from app.schemas.citation import Citation, CitationCreate, CitationUpdate
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.event import (
    AttendanceRecord,
    AttendanceRecordCreate,
    Event,
    EventCreate,
    EventWithStats,
)
from app.schemas.form import (
    Form,
    FormCreate,
    FormField,
    FormFieldCreate,
    FormSubmission,
    FormSubmissionCreate,
)
from app.schemas.task import Task, TaskAssignment, TaskAssignmentCreate, TaskCreate
from app.schemas.user import User, UserCreate, UserUpdate

__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "Task",
    "TaskCreate",
    "TaskAssignment",
    "TaskAssignmentCreate",
    "Article",
    "ArticleCreate",
    "ArticleUpdate",
    "ArticleStats",
    "ArticleWithStats",
    "Citation",
    "CitationCreate",
    "CitationUpdate",
    "Form",
    "FormCreate",
    "FormField",
    "FormFieldCreate",
    "FormSubmission",
    "FormSubmissionCreate",
    "Event",
    "EventCreate",
    "EventWithStats",
    "AttendanceRecord",
    "AttendanceRecordCreate",
    "ErrorResponse",
    "PaginatedResponse",
]
