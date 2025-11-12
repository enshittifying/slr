# API Specification v1.0

**Base URL:** `https://slr-api-xxxxx-uw.a.run.app/api/v1`
**Authentication:** Bearer token (Google OAuth JWT)
**Content-Type:** `application/json`

---

## Authentication

### POST /auth/verify
Verify if a user is authorized to access the system.

**Request:**
```json
{
  "email": "jstanford@stanford.edu"
}
```

**Response:**
```json
{
  "is_authorized": true,
  "user": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "email": "jstanford@stanford.edu",
    "full_name": "Jane Stanford",
    "role": "member_editor"
  }
}
```

---

## Users

### GET /users/me
Get current user profile.

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "email": "jstanford@stanford.edu",
  "full_name": "Jane Stanford",
  "role": "member_editor",
  "created_at": "2025-01-15T10:00:00Z",
  "last_login": "2025-11-12T14:30:00Z"
}
```

### GET /users
List all users (admin only).

**Query Parameters:**
- `role` (optional): Filter by role
- `is_active` (optional): Filter by active status
- `page` (default: 1)
- `per_page` (default: 50, max: 100)

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@stanford.edu",
      "full_name": "User Name",
      "role": "member_editor",
      "is_active": true
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 50
}
```

### POST /users
Create new user (admin only).

**Request:**
```json
{
  "email": "newuser@stanford.edu",
  "full_name": "New User",
  "role": "member_editor"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "newuser@stanford.edu",
  "full_name": "New User",
  "role": "member_editor",
  "created_at": "2025-11-12T14:35:00Z"
}
```

### PATCH /users/{user_id}
Update user (admin only, or self for limited fields).

**Request:**
```json
{
  "full_name": "Updated Name",
  "role": "senior_editor",
  "is_active": false
}
```

### DELETE /users/{user_id}
Soft delete user (admin only).

---

## Tasks

### GET /tasks
List all tasks for current user.

**Query Parameters:**
- `status` (optional): `not_started`, `in_progress`, `completed`, `blocked`
- `due_before` (optional): ISO 8601 date
- `due_after` (optional): ISO 8601 date
- `page`, `per_page`

**Response:**
```json
{
  "tasks": [
    {
      "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "title": "Review Article Submission #123",
      "description": "Perform initial read and provide feedback.",
      "due_date": "2024-10-26T00:00:00Z",
      "assignment": {
        "id": "assignment_uuid",
        "status": "in_progress",
        "assigned_at": "2024-10-20T10:00:00Z",
        "completed_at": null
      },
      "linked_form_id": null
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 50
}
```

### GET /tasks/{task_id}
Get task details.

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "title": "Review Article Submission #123",
  "description": "Perform initial read and provide feedback.",
  "due_date": "2024-10-26T00:00:00Z",
  "created_by": {
    "id": "uuid",
    "full_name": "Admin User"
  },
  "created_at": "2024-10-15T09:00:00Z",
  "assignments": [
    {
      "user": {
        "id": "uuid",
        "full_name": "Jane Stanford"
      },
      "status": "in_progress",
      "assigned_at": "2024-10-20T10:00:00Z"
    }
  ]
}
```

### POST /tasks
Create new task (admin/senior editor).

**Request:**
```json
{
  "title": "Review Article Submission #456",
  "description": "Substantive review required.",
  "due_date": "2024-12-01T00:00:00Z",
  "linked_form_id": null
}
```

### POST /tasks/{task_id}/assign
Assign task to users.

**Request:**
```json
{
  "user_ids": ["uuid1", "uuid2"]
}
```

**Response:**
```json
{
  "assignments": [
    {
      "id": "assignment_uuid1",
      "task_id": "task_uuid",
      "user_id": "uuid1",
      "status": "not_started",
      "assigned_at": "2025-11-12T14:40:00Z"
    }
  ]
}
```

### PATCH /tasks/{task_id}/assignments/{assignment_id}
Update assignment status.

**Request:**
```json
{
  "status": "completed",
  "notes": "Completed review. No issues found."
}
```

**Response:**
```json
{
  "id": "assignment_uuid",
  "status": "completed",
  "completed_at": "2025-11-12T14:45:00Z",
  "notes": "Completed review. No issues found."
}
```

---

## Articles

### GET /articles
List all articles.

**Query Parameters:**
- `status`: `draft`, `sp_in_progress`, `r1_in_progress`, `r2_in_progress`, `completed`, `published`
- `volume_number`, `issue_number`
- `assigned_editor`: User ID
- `page`, `per_page`

**Response:**
```json
{
  "articles": [
    {
      "id": "uuid",
      "title": "The Future of Legal AI",
      "author_name": "John Doe",
      "volume_number": 79,
      "issue_number": 1,
      "status": "r2_in_progress",
      "assigned_editor": {
        "id": "uuid",
        "full_name": "Jane Stanford"
      },
      "citation_count": 127,
      "citations_validated": 98,
      "submitted_at": "2025-09-01T10:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 50
}
```

### GET /articles/{article_id}
Get article details with citation summary.

**Response:**
```json
{
  "id": "uuid",
  "title": "The Future of Legal AI",
  "author_name": "John Doe",
  "volume_number": 79,
  "issue_number": 1,
  "status": "r2_in_progress",
  "assigned_editor": {
    "id": "uuid",
    "full_name": "Jane Stanford"
  },
  "submitted_at": "2025-09-01T10:00:00Z",
  "citation_stats": {
    "total": 127,
    "sp_completed": 127,
    "r1_completed": 115,
    "r2_completed": 98,
    "requires_manual_review": 12,
    "format_valid": 110,
    "support_valid": 105,
    "quote_valid": 118
  }
}
```

### POST /articles
Create new article (uploads citations separately).

**Request:**
```json
{
  "title": "AI and Legal Ethics",
  "author_name": "Jane Smith",
  "volume_number": 79,
  "issue_number": 2,
  "assigned_editor_id": "uuid"
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "AI and Legal Ethics",
  "author_name": "Jane Smith",
  "volume_number": 79,
  "issue_number": 2,
  "status": "draft",
  "created_at": "2025-11-12T14:50:00Z"
}
```

### POST /articles/{article_id}/citations/upload
Upload citations from file (CSV or parsed document).

**Request (multipart/form-data):**
```
file: citations.csv
```

**CSV Format:**
```csv
footnote_number,citation_text,proposition,source_type,source_title,source_author
1,"Doe v. Roe, 123 U.S. 456 (1990).","This case establishes...",case,"Doe v. Roe","Justice Smith"
2,"John Smith, Legal Theory 45 (2020).","The author argues...",book,"Legal Theory","John Smith"
```

**Response:**
```json
{
  "citations_created": 127,
  "errors": []
}
```

### POST /articles/{article_id}/pipeline/start
Start the citation pipeline (Stage 1: Sourcepull).

**Request:**
```json
{
  "stages": ["sp", "r1", "r2"]  // Or specific stages
}
```

**Response:**
```json
{
  "job_id": "job_uuid",
  "message": "Pipeline started for 127 citations",
  "estimated_completion": "2025-11-12T16:00:00Z"
}
```

---

## Citations

### GET /citations
List citations (with filters).

**Query Parameters:**
- `article_id` (required or optional depending on use case)
- `sp_status`, `r1_status`, `r2_status`
- `requires_manual_review`: `true`/`false`
- `format_valid`, `support_valid`, `quote_valid`: `true`/`false`/`null`
- `page`, `per_page`

**Response:**
```json
{
  "citations": [
    {
      "id": "uuid",
      "article_id": "article_uuid",
      "footnote_number": 1,
      "citation_text": "Doe v. Roe, 123 U.S. 456 (1990).",
      "proposition": "This case establishes that...",
      "source_type": "case",
      "sp_status": "completed",
      "r1_status": "completed",
      "r2_status": "completed",
      "format_valid": true,
      "support_valid": true,
      "quote_valid": true,
      "requires_manual_review": false
    }
  ],
  "total": 127,
  "page": 1,
  "per_page": 50
}
```

### GET /citations/{citation_id}
Get detailed citation with validation results.

**Response:**
```json
{
  "id": "uuid",
  "article_id": "article_uuid",
  "footnote_number": 42,
  "citation_text": "Smith v. Jones, 456 F.3d 789 (9th Cir. 2015).",
  "proposition": "The Ninth Circuit held that...",
  "source_type": "case",
  "source_title": "Smith v. Jones",
  "source_author": null,
  "source_url": "https://example.com/case",

  "sp_status": "completed",
  "sp_pdf_path": "gs://slr-pdfs/raw-sources/article_uuid/citation_uuid.pdf",
  "sp_completed_at": "2025-11-12T10:00:00Z",

  "r1_status": "completed",
  "r1_pdf_path": "gs://slr-pdfs/r1-prepared/article_uuid/citation_uuid.pdf",
  "r1_metadata": {
    "author": "Smith",
    "defendant": "Jones",
    "citation": "456 F.3d 789",
    "court": "9th Cir.",
    "year": "2015",
    "page_numbers": [5, 6]
  },
  "r1_completed_at": "2025-11-12T11:30:00Z",

  "r2_status": "completed",
  "r2_pdf_path": "gs://slr-pdfs/r2-validated/article_uuid/citation_uuid.pdf",
  "r2_validation_result": {
    "format": {
      "is_valid": true,
      "issues": [],
      "suggestions": []
    },
    "support": {
      "is_supported": true,
      "confidence": 0.92,
      "relevant_passages": [
        "The court held that..."
      ]
    },
    "quote": {
      "is_valid": true,
      "exact_matches": true
    }
  },
  "r2_completed_at": "2025-11-12T13:00:00Z",

  "format_valid": true,
  "support_valid": true,
  "quote_valid": true,
  "requires_manual_review": false,
  "manual_review_notes": null,

  "created_at": "2025-11-12T09:00:00Z",
  "updated_at": "2025-11-12T13:00:00Z"
}
```

### GET /citations/{citation_id}/pdf
Download PDF for a citation (stage specified).

**Query Parameters:**
- `stage`: `sp`, `r1`, `r2`

**Response:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="citation_42_r2.pdf"

[PDF binary data]
```

### PATCH /citations/{citation_id}
Update citation (manual corrections).

**Request:**
```json
{
  "citation_text": "Smith v. Jones, 456 F.3d 789, 791 (9th Cir. 2015).",
  "requires_manual_review": false,
  "manual_review_notes": "Reviewed by editor. Citation format corrected."
}
```

### POST /citations/{citation_id}/revalidate
Re-run R2 validation for a specific citation.

**Response:**
```json
{
  "message": "Revalidation queued",
  "job_id": "job_uuid"
}
```

---

## Forms

### GET /forms
List all forms.

**Response:**
```json
{
  "forms": [
    {
      "id": "uuid",
      "name": "event_attendance_confirmation",
      "title": "Event Attendance Confirmation",
      "description": "Confirm your attendance at upcoming events.",
      "is_active": true,
      "field_count": 3,
      "created_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### GET /forms/{form_id}
Get form definition with all fields.

**Response:**
```json
{
  "id": "uuid",
  "name": "event_attendance_confirmation",
  "title": "Event Attendance Confirmation",
  "description": "Confirm your attendance at upcoming events.",
  "is_active": true,
  "fields": [
    {
      "id": "field_uuid1",
      "field_type": "text",
      "label": "Full Name",
      "field_name": "full_name",
      "is_required": true,
      "display_order": 1
    },
    {
      "id": "field_uuid2",
      "field_type": "radio",
      "label": "Will you attend?",
      "field_name": "attendance_status",
      "is_required": true,
      "options": ["Yes", "No", "Maybe"],
      "display_order": 2
    }
  ]
}
```

### POST /forms
Create new form (admin only).

**Request:**
```json
{
  "name": "article_proposal",
  "title": "Article Proposal Form",
  "description": "Submit your article proposal for review.",
  "fields": [
    {
      "field_type": "text",
      "label": "Article Title",
      "field_name": "article_title",
      "is_required": true,
      "display_order": 1
    },
    {
      "field_type": "textarea",
      "label": "Abstract",
      "field_name": "abstract",
      "is_required": true,
      "display_order": 2
    }
  ]
}
```

### POST /forms/{form_id}/submissions
Submit form response.

**Request:**
```json
{
  "submission_data": {
    "full_name": "Jane Stanford",
    "attendance_status": "Yes"
  }
}
```

**Response:**
```json
{
  "id": "submission_uuid",
  "form_id": "form_uuid",
  "submitted_by": "user_uuid",
  "submitted_at": "2025-11-12T15:00:00Z"
}
```

### GET /forms/{form_id}/submissions
Get all submissions for a form (admin only).

**Query Parameters:**
- `submitted_by` (optional): User ID
- `submitted_after`, `submitted_before`
- `page`, `per_page`

**Response:**
```json
{
  "submissions": [
    {
      "id": "submission_uuid",
      "submitted_by": {
        "id": "user_uuid",
        "full_name": "Jane Stanford"
      },
      "submission_data": {
        "full_name": "Jane Stanford",
        "attendance_status": "Yes"
      },
      "submitted_at": "2025-11-12T15:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 50
}
```

---

## Events & Attendance

### GET /events
List all events.

**Query Parameters:**
- `event_after`, `event_before`: Filter by date
- `page`, `per_page`

**Response:**
```json
{
  "events": [
    {
      "id": "uuid",
      "title": "Fall Symposium 2025",
      "description": "Annual symposium discussion.",
      "event_date": "2025-11-20T18:00:00Z",
      "location": "Stanford Law School, Room 100",
      "attendance_form_id": "form_uuid",
      "attendee_count": 35,
      "response_rate": 0.85
    }
  ]
}
```

### POST /events
Create new event (admin/senior editor).

**Request:**
```json
{
  "title": "Winter Meeting 2026",
  "description": "Planning session for Volume 80.",
  "event_date": "2026-01-15T18:00:00Z",
  "location": "Stanford Law School, Room 200",
  "create_attendance_form": true
}
```

**Response:**
```json
{
  "id": "event_uuid",
  "title": "Winter Meeting 2026",
  "event_date": "2026-01-15T18:00:00Z",
  "google_calendar_event_id": "calendar_event_id",
  "attendance_form_id": "form_uuid",
  "attendance_form_url": "https://slr.stanford.edu/forms/form_uuid"
}
```

### POST /events/{event_id}/attendance
Record attendance (can be called directly or via form submission).

**Request:**
```json
{
  "user_id": "user_uuid",
  "status": "attending"
}
```

### GET /events/{event_id}/attendance
Get attendance list for event.

**Response:**
```json
{
  "event": {
    "id": "event_uuid",
    "title": "Fall Symposium 2025",
    "event_date": "2025-11-20T18:00:00Z"
  },
  "attendance": [
    {
      "user": {
        "id": "user_uuid",
        "full_name": "Jane Stanford"
      },
      "status": "attending",
      "confirmed_at": "2025-11-12T15:00:00Z"
    }
  ],
  "stats": {
    "total_invited": 50,
    "attending": 35,
    "not_attending": 10,
    "maybe": 3,
    "no_response": 2
  }
}
```

---

## System Configuration

### GET /config
Get all system configuration (admin only).

**Response:**
```json
{
  "config": {
    "google_calendar_id": "slr-calendar@stanford.edu",
    "default_notification_email": "slr-admin@stanford.edu",
    "max_upload_size_mb": 50,
    "pipeline_auto_start": true,
    "llm_model": "gpt-4o-mini",
    "llm_temperature": 0.1
  }
}
```

### PATCH /config
Update configuration (admin only).

**Request:**
```json
{
  "pipeline_auto_start": false,
  "llm_temperature": 0.2
}
```

---

## Pipeline Management

### GET /pipeline/jobs
List pipeline jobs.

**Query Parameters:**
- `article_id` (optional)
- `status`: `queued`, `in_progress`, `completed`, `failed`
- `page`, `per_page`

**Response:**
```json
{
  "jobs": [
    {
      "id": "job_uuid",
      "article_id": "article_uuid",
      "stage": "r2",
      "status": "in_progress",
      "citations_total": 127,
      "citations_processed": 98,
      "started_at": "2025-11-12T10:00:00Z",
      "estimated_completion": "2025-11-12T16:00:00Z"
    }
  ]
}
```

### GET /pipeline/jobs/{job_id}
Get job status and details.

**Response:**
```json
{
  "id": "job_uuid",
  "article_id": "article_uuid",
  "stage": "r2",
  "status": "completed",
  "citations_total": 127,
  "citations_processed": 127,
  "citations_succeeded": 115,
  "citations_failed": 0,
  "citations_manual_review": 12,
  "started_at": "2025-11-12T10:00:00Z",
  "completed_at": "2025-11-12T15:30:00Z",
  "errors": []
}
```

### POST /pipeline/jobs/{job_id}/cancel
Cancel a running job (admin only).

---

## Audit Log

### GET /audit
Get audit log (admin only).

**Query Parameters:**
- `user_id` (optional)
- `action` (optional): `create`, `update`, `delete`, `login`
- `table_name` (optional)
- `after`, `before`: ISO 8601 timestamps
- `page`, `per_page`

**Response:**
```json
{
  "logs": [
    {
      "id": 12345,
      "user": {
        "id": "user_uuid",
        "full_name": "Jane Stanford"
      },
      "action": "update",
      "table_name": "citations",
      "record_id": "citation_uuid",
      "old_values": {
        "r2_status": "in_progress"
      },
      "new_values": {
        "r2_status": "completed"
      },
      "ip_address": "171.64.1.1",
      "created_at": "2025-11-12T15:30:00Z"
    }
  ],
  "total": 5432,
  "page": 1,
  "per_page": 50
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```

### Common Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | `VALIDATION_ERROR` | Request validation failed |
| 401 | `UNAUTHORIZED` | Missing or invalid auth token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource already exists |
| 422 | `UNPROCESSABLE_ENTITY` | Cannot process request |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_SERVER_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

---

## Rate Limiting

- **Default:** 100 requests per minute per user
- **Admin:** 500 requests per minute
- **Pipeline triggers:** 10 per minute per user

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699800000
```

---

## Versioning

API is versioned via URL path: `/api/v1/...`

When v2 is released, v1 will be supported for 6 months minimum.

---

## WebSocket API (Real-time Updates)

**Endpoint:** `wss://slr-api-xxxxx-uw.a.run.app/ws`

**Connection:**
```javascript
const ws = new WebSocket('wss://slr-api-xxxxx-uw.a.run.app/ws');
ws.send(JSON.stringify({
  type: 'authenticate',
  token: 'jwt_token_here'
}));
```

**Message Types:**
```json
// Subscribe to article updates
{
  "type": "subscribe",
  "channel": "article:uuid"
}

// Received when citation status changes
{
  "type": "citation_updated",
  "data": {
    "citation_id": "uuid",
    "r2_status": "completed",
    "requires_manual_review": false
  }
}

// Received when pipeline job progresses
{
  "type": "job_progress",
  "data": {
    "job_id": "uuid",
    "citations_processed": 50,
    "citations_total": 127
  }
}
```

---

## Pagination

All list endpoints support pagination:

**Request:**
```
GET /api/v1/tasks?page=2&per_page=25
```

**Response includes:**
```json
{
  "tasks": [...],
  "total": 127,
  "page": 2,
  "per_page": 25,
  "total_pages": 6,
  "links": {
    "first": "/api/v1/tasks?page=1&per_page=25",
    "prev": "/api/v1/tasks?page=1&per_page=25",
    "next": "/api/v1/tasks?page=3&per_page=25",
    "last": "/api/v1/tasks?page=6&per_page=25"
  }
}
```

---

## OpenAPI Specification

Full OpenAPI 3.0 specification auto-generated at:
- **Swagger UI:** `https://slr-api-xxxxx-uw.a.run.app/docs`
- **ReDoc:** `https://slr-api-xxxxx-uw.a.run.app/redoc`
- **JSON:** `https://slr-api-xxxxx-uw.a.run.app/openapi.json`
