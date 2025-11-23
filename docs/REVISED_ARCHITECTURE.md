# Revised Architecture: Stanford Law Review Workflow Management System

## Executive Summary

**Architecture Decision:** Moving from Google Apps Script to a **Python/Flask + PostgreSQL** architecture to properly handle concurrent users and provide scalability.

### Why Not Google Apps Script?
- **Concurrency Issues**: LockService serializes all writes, creating bottlenecks with multiple concurrent users
- **Quota Limitations**: 6-minute execution limit, limited daily trigger runtime
- **Scalability**: Not designed for high-traffic applications
- **Development Constraints**: Limited debugging, testing, and version control capabilities

## New Tech Stack

### Backend
- **Framework**: Flask (Python 3.9+)
  - Lightweight, flexible
  - Excellent for Vercel serverless deployment
  - Strong ecosystem for integrations
- **Database**: PostgreSQL 14+
  - ACID compliance with proper transaction handling
  - Row-level locking for concurrent access
  - Robust performance under load
  - Can use **Vercel Postgres** for managed hosting
- **ORM**: SQLAlchemy 2.0+
  - Type-safe models
  - Migration support via Alembic
- **Authentication**: Flask-Login + Google OAuth 2.0
  - Session management
  - Domain-restricted (@stanford.edu)

### Frontend
- **Option A**: Flask + Jinja2 templates (simpler, server-rendered)
- **Option B**: React SPA (modern, more interactive)
- **Recommendation**: Start with Flask templates, migrate to React if needed

### External Integrations
- **Google Workspace APIs** (via Python client libraries):
  - Google Sheets API (for legacy compatibility and data export)
  - Google Drive API (PDF storage)
  - Google Calendar API (event management)
  - Google Forms API (form generation)
- **LLM APIs**:
  - OpenAI API (GPT-4)
  - Anthropic API (Claude)

### Deployment
- **Platform**: Vercel
  - Serverless Python functions
  - Edge network for low latency
  - Free tier suitable for development
  - Easy GitHub integration
- **Database**: Vercel Postgres OR external PostgreSQL (e.g., Supabase, Railway)
- **File Storage**: Google Drive (existing integration) OR Vercel Blob Storage

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  Flask Templates (Jinja2) + Bootstrap CSS                   │
│  - Dashboard, Task Management, Form Builder                  │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/REST API
┌────────────────▼────────────────────────────────────────────┐
│                      FLASK BACKEND                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Routes (/api/tasks, /api/forms, /api/auth)      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Business Logic Layer                                 │   │
│  │  - Task Manager, Form Manager, Auth Manager          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Data Access Layer (SQLAlchemy Models)                │   │
│  └──────────────────────────────────────────────────────┘   │
└────┬─────────────────────────────┬──────────────────────────┘
     │                             │
     │ PostgreSQL                  │ Google APIs
     │ Connection                  │ (Sheets, Drive, Calendar)
     │                             │
┌────▼─────────────────┐    ┌─────▼──────────────────────────┐
│   PostgreSQL DB      │    │   Google Workspace             │
│                      │    │   - Sheets (data export)       │
│  - users             │    │   - Drive (PDF storage)        │
│  - tasks             │    │   - Calendar (events)          │
│  - assignments       │    │   - Forms (generation)         │
│  - form_definitions  │    └────────────────────────────────┘
│  - form_submissions  │
│  - attendance_log    │
└──────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   PIPELINE MACHINES                          │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  sp_machine   │→ │  r1_machine  │→ │  r2_machine  │     │
│  │  (Python CLI) │  │  (Python CLI)│  │  (Python CLI)│     │
│  └───────────────┘  └──────────────┘  └──────────────┘     │
│          ↓                  ↓                  ↓             │
│      Raw PDFs          R1 PDFs          R2 Validated        │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Core Tables

```sql
-- Users (Member Editors)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('member_editor', 'senior_editor', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    due_date DATE,
    linked_form_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assignments (many-to-many: users ↔ tasks)
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'not_started'
        CHECK (status IN ('not_started', 'in_progress', 'completed')),
    date_completed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, task_id)
);

-- Form Definitions
CREATE TABLE form_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_name VARCHAR(255) NOT NULL,
    google_form_id VARCHAR(255),
    item_id INTEGER,
    question_title TEXT,
    item_type VARCHAR(50) CHECK (item_type IN ('text', 'multiple_choice', 'checkbox', 'date')),
    options TEXT, -- JSON array for choices
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Form Submissions
CREATE TABLE form_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    responses JSONB NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance Log
CREATE TABLE attendance_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    event_name VARCHAR(500) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    status VARCHAR(50) CHECK (status IN ('attending', 'not_attending', 'maybe')),
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Config (key-value store)
CREATE TABLE system_config (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_assignments_user_id ON assignments(user_id);
CREATE INDEX idx_assignments_task_id ON assignments(task_id);
CREATE INDEX idx_assignments_status ON assignments(status);
CREATE INDEX idx_form_submissions_form_id ON form_submissions(form_id);
CREATE INDEX idx_attendance_user_id ON attendance_log(user_id);
```

## Concurrency Handling

### PostgreSQL Transactions (replaces Google Apps Script LockService)

```python
from sqlalchemy.orm import Session

# Example: Update task status with proper locking
def update_task_status(db: Session, assignment_id: str, new_status: str):
    with db.begin():  # Start transaction
        # SELECT ... FOR UPDATE locks the row
        assignment = db.query(Assignment).filter(
            Assignment.id == assignment_id
        ).with_for_update().first()

        if not assignment:
            raise ValueError("Assignment not found")

        assignment.status = new_status
        if new_status == 'completed':
            assignment.date_completed = datetime.utcnow()

        db.commit()  # Atomic commit

    return assignment
```

**Benefits over LockService:**
- Row-level locking (not script-wide)
- Multiple users can update different rows simultaneously
- ACID guarantees
- Automatic deadlock detection

## Deployment to Vercel

### Project Structure
```
slr/
├── api/                      # Vercel serverless functions
│   ├── __init__.py
│   ├── index.py             # Main Flask app entry point
│   └── routes/
│       ├── auth.py
│       ├── tasks.py
│       ├── forms.py
│       └── attendance.py
├── web_app/                 # Main Flask application
│   ├── __init__.py
│   ├── models/              # SQLAlchemy models
│   ├── services/            # Business logic
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS, images
├── sp_machine/              # Pipeline stage 1
├── r1_machine/              # Pipeline stage 2
├── r2_machine/              # Pipeline stage 3
├── shared_utils/            # Shared utilities
├── migrations/              # Alembic migrations
├── vercel.json              # Vercel configuration
├── requirements.txt
└── .env.example
```

### Vercel Configuration (`vercel.json`)

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production"
  }
}
```

## Migration Path

### Phase 1: Core Infrastructure (Week 1-2)
1. ✅ Set up PostgreSQL database
2. ✅ Implement SQLAlchemy models
3. ✅ Create Flask app structure
4. ✅ Implement authentication (Google OAuth)
5. ✅ Deploy to Vercel

### Phase 2: Task Management (Week 3)
1. Task CRUD operations
2. Assignment management
3. Dashboard UI
4. Google Sheets sync (read/write for compatibility)

### Phase 3: Form Engine (Week 4)
1. Dynamic form generation (Google Forms API)
2. Form submission handling
3. Attendance tracking

### Phase 4: Pipeline Integration (Week 5-6)
1. sp_machine integration
2. r1_machine implementation
3. r2_machine implementation
4. End-to-end testing

## Key Advantages of New Architecture

| Feature | Google Apps Script | Python/Flask + PostgreSQL |
|---------|-------------------|---------------------------|
| Concurrent Users | ⚠️ Serialized writes | ✅ Row-level locking |
| Execution Time | ⚠️ 6-min limit | ✅ No hard limit |
| Database | ⚠️ Google Sheets | ✅ PostgreSQL (ACID) |
| Testing | ⚠️ Limited | ✅ Full unit/integration tests |
| Version Control | ⚠️ Via clasp | ✅ Native Git |
| Debugging | ⚠️ Limited | ✅ Full debugging tools |
| Scalability | ⚠️ ~100 users | ✅ Thousands of users |
| Cost | ✅ Free (Workspace) | ✅ Free tier (Vercel) |

## Next Steps

1. Configure Vercel project
2. Set up PostgreSQL database (Vercel Postgres or external)
3. Implement database models and migrations
4. Build Flask API
5. Create frontend templates
6. Test concurrent user scenarios
7. Deploy to production
