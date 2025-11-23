# Production Architecture: Stanford Law Review Citation System

**Date:** 2025-11-12
**Status:** Recommended Architecture
**Stack:** Cloud SQL (PostgreSQL), Cloud Run, Vercel, Cloud Functions, Pub/Sub

---

## Executive Summary

This architecture replaces the Google Sheets-based approach with a **production-grade, scalable system** that can handle hundreds of concurrent users and thousands of citations per article. Total estimated cost: **$30-50/month** for moderate usage (100 users, 500 articles/year).

### Key Improvements Over Original Design

| Aspect | Original | Production |
|--------|----------|------------|
| Database | Google Sheets | PostgreSQL (Cloud SQL) |
| Concurrency | LockService (30s waits) | Database transactions |
| Frontend | Google Apps Script | React/Next.js on Vercel (free) |
| Backend | Apps Script | Node.js/Python on Cloud Run |
| Pipeline | Undefined | Cloud Functions + Pub/Sub |
| Monitoring | Error log tab | Cloud Monitoring + Sentry |
| Scalability | ~50 users | 1000+ users |
| Data integrity | Eventually consistent | ACID transactions |
| Query performance | O(n) table scans | Indexed queries, O(log n) |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND TIER                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Next.js App on Vercel (FREE)                          │    │
│  │  - Member dashboard                                     │    │
│  │  - Task management UI                                   │    │
│  │  - Form builder interface                              │    │
│  │  - Real-time updates via WebSockets                    │    │
│  └─────────────────────┬──────────────────────────────────┘    │
└────────────────────────┼─────────────────────────────────────────┘
                         │ HTTPS/WSS
                         │ (OAuth 2.0 + JWT)
┌────────────────────────┼─────────────────────────────────────────┐
│                        │  APPLICATION TIER                        │
│  ┌─────────────────────▼──────────────────────────────────┐    │
│  │  Cloud Run API (Node.js/Python FastAPI)               │    │
│  │  - REST API endpoints                                  │    │
│  │  - GraphQL API (optional)                             │    │
│  │  - Authentication middleware                           │    │
│  │  - Rate limiting, caching                             │    │
│  │  - Autoscales 0 → N instances                         │    │
│  └─────────────────────┬──────────────────────────────────┘    │
└────────────────────────┼─────────────────────────────────────────┘
                         │
                         │ Connection Pool
┌────────────────────────┼─────────────────────────────────────────┐
│                        │  DATA TIER                               │
│  ┌─────────────────────▼──────────────────────────────────┐    │
│  │  Cloud SQL (PostgreSQL 15)                             │    │
│  │  - db-f1-micro: $7/month (dev/staging)                │    │
│  │  - db-g1-small: $25/month (production)                │    │
│  │  - Automated backups (7-day retention)                │    │
│  │  - Point-in-time recovery                             │    │
│  │  - High availability (optional +$50/mo)               │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE TIER (Event-Driven)                  │
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  Stage 1:    │      │  Stage 2:    │      │  Stage 3:    │  │
│  │  sp_machine  │      │  R1 Machine  │      │  r2_pipeline │  │
│  │  (Cloud Fn)  │─────▶│  (Cloud Fn)  │─────▶│  (Cloud Fn)  │  │
│  │              │      │              │      │              │  │
│  │  Retrieve    │      │  Prepare +   │      │  Validate    │  │
│  │  PDFs from   │      │  Redbox      │      │  Citations   │  │
│  │  sources     │      │  metadata    │      │  w/ LLM      │  │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘  │
│         │                     │                     │           │
│         │ Pub/Sub             │ Pub/Sub             │           │
│         │ Topic               │ Topic               │           │
│         │                     │                     │           │
│  ┌──────▼──────────────────────▼──────────────────▼───────┐   │
│  │  Cloud Storage (PDF Storage)                            │   │
│  │  - raw-sources/      (Stage 1 output)                  │   │
│  │  - r1-prepared/      (Stage 2 output)                  │   │
│  │  - r2-validated/     (Stage 3 output)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY TIER                            │
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐   │
│  │ Cloud Logging  │  │ Cloud          │  │ Sentry          │   │
│  │ - All logs     │  │ Monitoring     │  │ - Error         │   │
│  │ - Structured   │  │ - Metrics      │  │   tracking      │   │
│  │ - Searchable   │  │ - Alerts       │  │ - Performance   │   │
│  │                │  │ - Dashboards   │  │ - Free tier OK  │   │
│  └────────────────┘  └────────────────┘  └─────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Cloud Trace (Request tracing across services)           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Frontend: Vercel (FREE for this use case)

### Technology Stack
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **UI Library:** shadcn/ui + Tailwind CSS
- **State Management:** React Query (TanStack Query) for server state
- **Auth:** NextAuth.js with Google OAuth
- **Deployment:** Vercel (Free tier: unlimited hobby projects)

### Why Vercel?
```
✅ FREE for non-commercial projects
✅ Automatic HTTPS
✅ Global CDN
✅ Automatic deployments from Git
✅ Preview deployments for PRs
✅ Built-in analytics
✅ Edge functions for API routes
✅ Perfect for Next.js (same company)
```

### Vercel Free Tier Limits (All Fine for This Project)
- 100 GB bandwidth/month ✅
- 100 hours serverless function execution ✅
- Unlimited websites ✅
- Commercial use requires Pro ($20/user/month) - but Stanford = educational ✅

### Project Structure
```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── callback/
│   ├── (dashboard)/
│   │   ├── tasks/
│   │   ├── forms/
│   │   ├── attendance/
│   │   └── citations/
│   └── api/
│       └── auth/[...nextauth]/
├── components/
│   ├── ui/           # shadcn components
│   ├── tasks/
│   ├── forms/
│   └── citations/
├── lib/
│   ├── api-client.ts # API wrapper with auth
│   ├── auth.ts       # NextAuth config
│   └── hooks/        # React Query hooks
└── middleware.ts     # Auth middleware
```

### Key Features
- **Real-time updates** via WebSocket (or React Query polling)
- **Optimistic updates** for better UX
- **Offline support** with service workers (optional)
- **SSR for SEO** (not critical here, but free)

---

## 2. Backend API: Cloud Run

### Technology Stack
- **Framework:** FastAPI (Python) or Express (Node.js)
- **Language:** Python 3.11 (for consistency with pipeline)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migration Tool:** Alembic
- **Validation:** Pydantic v2
- **API Docs:** Auto-generated OpenAPI (Swagger)

### Why FastAPI?
- Modern, fast, async Python framework
- Automatic API docs
- Type safety with Pydantic
- Easy to integrate with pipeline code
- Better performance than Flask/Django for APIs

### API Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Environment config
│   ├── database.py          # DB connection pool
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── citation.py
│   │   └── form.py
│   ├── schemas/             # Pydantic schemas (API contracts)
│   │   ├── user.py
│   │   ├── task.py
│   │   └── citation.py
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py      # /api/v1/auth/*
│   │   │   ├── tasks.py     # /api/v1/tasks/*
│   │   │   ├── forms.py     # /api/v1/forms/*
│   │   │   ├── citations.py # /api/v1/citations/*
│   │   │   └── users.py     # /api/v1/users/*
│   │   └── deps.py          # Dependency injection
│   ├── services/            # Business logic
│   │   ├── task_service.py
│   │   ├── form_service.py
│   │   └── citation_service.py
│   └── middleware/
│       ├── auth.py          # JWT verification
│       ├── rate_limit.py    # Rate limiting
│       └── logging.py       # Request logging
├── alembic/                 # Database migrations
│   └── versions/
├── tests/
│   ├── test_api/
│   └── test_services/
├── Dockerfile               # Multi-stage build
├── requirements.txt
└── pyproject.toml
```

### Cloud Run Configuration
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: slr-api
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/launch-stage: BETA
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: '0'     # Scale to zero
        autoscaling.knative.dev/maxScale: '100'
        run.googleapis.com/cpu-throttling: 'true' # Save costs
    spec:
      containerConcurrency: 80  # Requests per instance
      timeoutSeconds: 300       # 5 min max (for long pipeline triggers)
      containers:
      - image: gcr.io/PROJECT_ID/slr-api:latest
        resources:
          limits:
            cpu: '1'
            memory: 512Mi
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-url
              key: url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-key
              key: api-key
```

### Cost Estimate (Cloud Run)
```
Free tier: 2 million requests/month, 360k GB-seconds
Typical usage: ~50k requests/month
Cost: $0/month (within free tier) to ~$5/month
```

---

## 3. Database: Cloud SQL (PostgreSQL)

### Instance Configuration

**Development/Staging:**
```
Instance: db-f1-micro
- 1 shared vCPU
- 614 MB RAM
- 10 GB storage
Cost: ~$7/month
```

**Production:**
```
Instance: db-g1-small
- 1 shared vCPU
- 1.7 GB RAM
- 20 GB storage
- Automated backups
- 7-day point-in-time recovery
Cost: ~$25/month
```

### Database Schema

```sql
-- Core user management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('member_editor', 'senior_editor', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Tasks (master list)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    linked_form_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);

-- Task assignments (many-to-many)
CREATE TABLE task_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'not_started'
        CHECK (status IN ('not_started', 'in_progress', 'completed', 'blocked')),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    UNIQUE(task_id, user_id)
);

CREATE INDEX idx_assignments_user_status ON task_assignments(user_id, status);
CREATE INDEX idx_assignments_task ON task_assignments(task_id);

-- Articles and citations (core domain model)
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(1000) NOT NULL,
    author_name VARCHAR(500),
    volume_number INTEGER NOT NULL,
    issue_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'sp_in_progress', 'r1_in_progress', 'r2_in_progress', 'completed', 'published')),
    submitted_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    assigned_editor UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_articles_volume_issue ON articles(volume_number, issue_number);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_editor ON articles(assigned_editor);

CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    footnote_number INTEGER NOT NULL,
    citation_text TEXT NOT NULL,
    proposition TEXT, -- The claim the author is making

    -- Source information
    source_type VARCHAR(100), -- case, statute, book, article, etc.
    source_title VARCHAR(1000),
    source_author VARCHAR(500),
    source_url VARCHAR(2000),

    -- Pipeline tracking
    sp_status VARCHAR(50) DEFAULT 'pending'
        CHECK (sp_status IN ('pending', 'in_progress', 'completed', 'failed', 'manual_required')),
    sp_pdf_path VARCHAR(1000), -- Cloud Storage path
    sp_completed_at TIMESTAMP WITH TIME ZONE,

    r1_status VARCHAR(50) DEFAULT 'pending'
        CHECK (r1_status IN ('pending', 'in_progress', 'completed', 'failed', 'manual_required')),
    r1_pdf_path VARCHAR(1000),
    r1_metadata JSONB, -- Extracted metadata (author, title, page numbers, etc.)
    r1_completed_at TIMESTAMP WITH TIME ZONE,

    r2_status VARCHAR(50) DEFAULT 'pending'
        CHECK (r2_status IN ('pending', 'in_progress', 'completed', 'failed', 'manual_required')),
    r2_pdf_path VARCHAR(1000),
    r2_validation_result JSONB, -- LLM validation output
    r2_completed_at TIMESTAMP WITH TIME ZONE,

    -- Validation flags
    format_valid BOOLEAN,
    support_valid BOOLEAN,
    quote_valid BOOLEAN,
    requires_manual_review BOOLEAN DEFAULT FALSE,
    manual_review_notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(article_id, footnote_number)
);

CREATE INDEX idx_citations_article ON citations(article_id);
CREATE INDEX idx_citations_sp_status ON citations(sp_status);
CREATE INDEX idx_citations_r1_status ON citations(r1_status);
CREATE INDEX idx_citations_r2_status ON citations(r2_status);
CREATE INDEX idx_citations_manual_review ON citations(requires_manual_review) WHERE requires_manual_review = TRUE;

-- Forms system
CREATE TABLE forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE form_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    field_type VARCHAR(50) NOT NULL
        CHECK (field_type IN ('text', 'textarea', 'email', 'number', 'date', 'select', 'multiselect', 'checkbox', 'radio')),
    label VARCHAR(500) NOT NULL,
    field_name VARCHAR(100) NOT NULL, -- Programmatic name
    is_required BOOLEAN DEFAULT FALSE,
    options JSONB, -- For select/radio/checkbox
    validation_rules JSONB,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(form_id, field_name)
);

CREATE INDEX idx_form_fields_form ON form_fields(form_id, display_order);

CREATE TABLE form_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    submitted_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submission_data JSONB NOT NULL, -- Flexible JSON storage of answers
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_submissions_form ON form_submissions(form_id);
CREATE INDEX idx_submissions_user ON form_submissions(submitted_by);
CREATE INDEX idx_submissions_date ON form_submissions(submitted_at);

-- Attendance tracking
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    event_date TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(500),
    google_calendar_event_id VARCHAR(255),
    attendance_form_id UUID REFERENCES forms(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_date ON events(event_date);

CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL
        CHECK (status IN ('attending', 'not_attending', 'maybe', 'no_response')),
    confirmed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(event_id, user_id)
);

CREATE INDEX idx_attendance_event ON attendance_records(event_id);
CREATE INDEX idx_attendance_user ON attendance_records(user_id);

-- System configuration (key-value store)
CREATE TABLE system_config (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Audit log (immutable)
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- create, update, delete, login, etc.
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_citations_updated_at BEFORE UPDATE ON citations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add more triggers for other tables...
```

### Database Migrations
```bash
# Using Alembic
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Connection Pooling
```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Connection pool config for Cloud SQL
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,          # Max 5 connections per Cloud Run instance
    max_overflow=10,      # Allow 10 extra connections during spikes
    pool_pre_ping=True,   # Verify connections before use
    pool_recycle=3600,    # Recycle connections after 1 hour
    echo=False            # Set True for SQL debugging
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

---

## 4. Pipeline Infrastructure: Cloud Functions + Pub/Sub

### Event-Driven Architecture

```
Article submitted
    ↓
API creates citations records (status: 'pending')
    ↓
API publishes message to 'sp-queue' topic
    ↓
Stage 1 Cloud Function triggered
    ↓
Processes citations, downloads PDFs
    ↓
Updates DB: sp_status = 'completed'
    ↓
Publishes to 'r1-queue' topic
    ↓
Stage 2 Cloud Function triggered
    ↓
... and so on
```

### Pub/Sub Topics & Subscriptions

```bash
# Create topics
gcloud pubsub topics create sp-queue
gcloud pubsub topics create r1-queue
gcloud pubsub topics create r2-queue
gcloud pubsub topics create dlq-queue  # Dead Letter Queue for failures

# Create subscriptions with retry policy
gcloud pubsub subscriptions create sp-queue-sub \
    --topic=sp-queue \
    --ack-deadline=600 \
    --retry-minimum-backoff=10s \
    --retry-maximum-backoff=600s \
    --max-delivery-attempts=5 \
    --dead-letter-topic=dlq-queue
```

### Cloud Function: Stage 1 (sp_machine)

```python
# functions/sp_machine/main.py
import functions_framework
from google.cloud import pubsub_v1, storage
from sqlalchemy import select
import asyncio
from models import Citation
from services.pdf_retrieval import retrieve_pdf

publisher = pubsub_v1.PublisherClient()
storage_client = storage.Client()

@functions_framework.cloud_event
def handle_sp_queue(cloud_event):
    """
    Triggered by Pub/Sub message from sp-queue topic.

    Message format:
    {
        "citation_ids": ["uuid1", "uuid2", ...],
        "article_id": "uuid"
    }
    """
    message_data = cloud_event.data["message"]["data"]
    payload = json.loads(base64.b64decode(message_data))

    citation_ids = payload["citation_ids"]
    article_id = payload["article_id"]

    try:
        # Process each citation
        for citation_id in citation_ids:
            process_citation(citation_id)

        # Publish to next stage
        publisher.publish(
            "projects/PROJECT_ID/topics/r1-queue",
            json.dumps(payload).encode(),
            citation_ids=",".join(citation_ids)
        )

    except Exception as e:
        # Log error and let Pub/Sub retry
        print(f"Error processing citations: {e}")
        raise  # Causes message to be redelivered

def process_citation(citation_id: str):
    """Retrieve PDF for a single citation."""
    # 1. Fetch citation from database
    citation = db.query(Citation).filter(Citation.id == citation_id).first()

    # 2. Update status to in_progress
    citation.sp_status = "in_progress"
    db.commit()

    try:
        # 3. Retrieve PDF using appropriate puller
        pdf_bytes = retrieve_pdf(citation.citation_text, citation.source_type)

        # 4. Upload to Cloud Storage
        bucket = storage_client.bucket("slr-pdfs")
        blob_path = f"raw-sources/{citation.article_id}/{citation_id}.pdf"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(pdf_bytes, content_type="application/pdf")

        # 5. Update database
        citation.sp_status = "completed"
        citation.sp_pdf_path = f"gs://slr-pdfs/{blob_path}"
        citation.sp_completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        # Mark as failed, will retry via Pub/Sub
        citation.sp_status = "failed"
        db.commit()
        raise
```

### Cloud Function: Stage 2 (r1_machine)

```python
# functions/r1_machine/main.py
import functions_framework
from google.cloud import storage, vision
import fitz  # PyMuPDF

@functions_framework.cloud_event
def handle_r1_queue(cloud_event):
    """
    Process raw PDFs: clean, extract metadata, redbox.
    """
    message_data = cloud_event.data["message"]["data"]
    payload = json.loads(base64.b64decode(message_data))

    for citation_id in payload["citation_ids"]:
        process_r1(citation_id)

    # Publish to R2 stage
    publisher.publish(
        "projects/PROJECT_ID/topics/r2-queue",
        json.dumps(payload).encode()
    )

def process_r1(citation_id: str):
    """Prepare PDF and extract metadata."""
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    citation.r1_status = "in_progress"
    db.commit()

    try:
        # 1. Download PDF from Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket("slr-pdfs")
        blob = bucket.blob(citation.sp_pdf_path.replace("gs://slr-pdfs/", ""))
        pdf_bytes = blob.download_as_bytes()

        # 2. Process PDF: remove cover pages, clean
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        # ... cleaning logic ...

        # 3. Extract metadata using OCR/NLP
        vision_client = vision.ImageAnnotatorClient()
        metadata = extract_metadata(doc, vision_client)

        # 4. Draw red boxes around metadata
        doc = draw_redboxes(doc, metadata)

        # 5. Save R1 PDF
        r1_pdf_bytes = doc.write()
        r1_blob_path = f"r1-prepared/{citation.article_id}/{citation_id}.pdf"
        r1_blob = bucket.blob(r1_blob_path)
        r1_blob.upload_from_string(r1_pdf_bytes, content_type="application/pdf")

        # 6. Update database
        citation.r1_status = "completed"
        citation.r1_pdf_path = f"gs://slr-pdfs/{r1_blob_path}"
        citation.r1_metadata = metadata  # Store as JSONB
        citation.r1_completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        citation.r1_status = "failed"
        db.commit()
        raise
```

### Cloud Function: Stage 3 (r2_pipeline)

```python
# functions/r2_pipeline/main.py
import functions_framework
from openai import AsyncOpenAI
from services.citation_validator import validate_citation_format
from services.support_checker import check_proposition_support

openai_client = AsyncOpenAI()

@functions_framework.cloud_event
def handle_r2_queue(cloud_event):
    """
    Final validation: check formatting, verify support, generate R2 docs.
    """
    message_data = cloud_event.data["message"]["data"]
    payload = json.loads(base64.b64decode(message_data))

    for citation_id in payload["citation_ids"]:
        process_r2(citation_id)

async def process_r2(citation_id: str):
    """Validate citation using LLM."""
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    citation.r2_status = "in_progress"
    db.commit()

    try:
        # 1. Load R1 PDF and extract text
        pdf_text = extract_text_from_r1_pdf(citation.r1_pdf_path)

        # 2. Load Bluebook/Redbook rules
        rules = load_citation_rules(citation.source_type)

        # 3. Validate citation formatting
        format_result = await validate_citation_format(
            citation.citation_text,
            rules,
            openai_client
        )

        # 4. Check proposition support
        support_result = await check_proposition_support(
            citation.proposition,
            pdf_text,
            openai_client
        )

        # 5. Verify quotes (exact string matching)
        quote_result = verify_quotes(citation.citation_text, pdf_text)

        # 6. Generate R2 PDF with annotations
        r2_pdf_bytes = generate_r2_pdf(
            citation.r1_pdf_path,
            format_result,
            support_result,
            quote_result
        )

        # 7. Upload R2 PDF
        bucket = storage_client.bucket("slr-pdfs")
        r2_blob_path = f"r2-validated/{citation.article_id}/{citation_id}.pdf"
        blob = bucket.blob(r2_blob_path)
        blob.upload_from_string(r2_pdf_bytes, content_type="application/pdf")

        # 8. Update database with results
        citation.r2_status = "completed"
        citation.r2_pdf_path = f"gs://slr-pdfs/{r2_blob_path}"
        citation.format_valid = format_result["is_valid"]
        citation.support_valid = support_result["is_supported"]
        citation.quote_valid = quote_result["is_valid"]
        citation.requires_manual_review = not all([
            format_result["is_valid"],
            support_result["is_supported"],
            quote_result["is_valid"]
        ])
        citation.r2_validation_result = {
            "format": format_result,
            "support": support_result,
            "quote": quote_result
        }
        citation.r2_completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        citation.r2_status = "failed"
        db.commit()
        raise
```

### Cloud Functions Configuration

```yaml
# functions/sp_machine/function.yaml
runtime: python311
entry_point: handle_sp_queue
timeout: 540s  # 9 minutes (max)
memory: 512MB
environment_variables:
  DATABASE_URL: projects/PROJECT_ID/secrets/database-url/versions/latest

trigger:
  event_type: google.cloud.pubsub.topic.v1.messagePublished
  resource: projects/PROJECT_ID/topics/sp-queue

service_account: citation-pipeline@PROJECT_ID.iam.gserviceaccount.com
```

### Cost Estimate (Cloud Functions + Pub/Sub)
```
Cloud Functions:
- 2 million invocations/month free
- Typical: ~5k invocations/month (500 articles × 10 citations × 3 stages)
- Cost: $0/month (within free tier)

Pub/Sub:
- 10 GB data free/month
- Typical: <1 GB/month
- Cost: $0/month
```

---

## 5. Observability & Monitoring

### Cloud Logging (Structured Logs)

```python
# backend/app/middleware/logging.py
import logging
from google.cloud import logging as cloud_logging

# Set up Cloud Logging
logging_client = cloud_logging.Client()
logging_client.setup_logging()

logger = logging.getLogger("slr-api")

# Structured logging
logger.info(
    "Citation processed",
    extra={
        "citation_id": citation_id,
        "article_id": article_id,
        "stage": "r2",
        "duration_ms": 1234,
        "status": "completed"
    }
)
```

### Cloud Monitoring (Dashboards & Alerts)

```yaml
# monitoring/alerts.yaml
displayName: "Citation Pipeline Alerts"

alerts:
  - displayName: "High Error Rate in Pipeline"
    conditions:
      - displayName: "Error rate > 5%"
        conditionThreshold:
          filter: |
            resource.type="cloud_function"
            severity="ERROR"
          comparison: COMPARISON_GT
          thresholdValue: 5
          duration: 300s
    notificationChannels:
      - email: slr-dev-team@stanford.edu
      - slack: slr-alerts-webhook

  - displayName: "API Response Time Slow"
    conditions:
      - displayName: "P95 latency > 2s"
        conditionThreshold:
          filter: |
            resource.type="cloud_run_revision"
            metric.type="run.googleapis.com/request_latencies"
          aggregations:
            - alignmentPeriod: 60s
              perSeriesAligner: ALIGN_DELTA
            - crossSeriesReducer: REDUCE_PERCENTILE_95
          comparison: COMPARISON_GT
          thresholdValue: 2000
          duration: 300s

  - displayName: "Database Connection Pool Exhausted"
    conditions:
      - displayName: "Active connections > 80% of pool"
        conditionThreshold:
          filter: |
            resource.type="cloudsql_database"
            metric.type="cloudsql.googleapis.com/database/postgresql/num_backends"
          comparison: COMPARISON_GT
          thresholdValue: 40  # 80% of 50 connection limit
```

### Sentry (Error Tracking)

```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment="production",
    traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
    profiles_sample_rate=0.1,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration()
    ]
)

# Automatic error reporting with context
@app.get("/api/v1/citations/{citation_id}")
async def get_citation(citation_id: str, current_user: User = Depends(get_current_user)):
    with sentry_sdk.start_transaction(op="http.server", name="GET /api/v1/citations"):
        # Transaction automatically tracked
        citation = await citation_service.get_by_id(citation_id)
        if not citation:
            # Error automatically sent to Sentry
            raise HTTPException(status_code=404, detail="Citation not found")
        return citation
```

### Cloud Trace (Distributed Tracing)

```python
# Automatic tracing for Cloud Run + Cloud Functions
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

tracer_provider = TracerProvider()
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
trace.set_tracer_provider(tracer_provider)

# Usage: automatically instruments FastAPI, SQLAlchemy, HTTP requests
```

### Monitoring Dashboard

```
Key Metrics to Monitor:
✓ API request rate, latency (p50, p95, p99)
✓ Error rate by endpoint
✓ Database connection pool usage
✓ Citation pipeline throughput (citations/hour)
✓ Pipeline stage completion times
✓ LLM API latency and cost
✓ Cloud Storage usage and egress
✓ Manual review queue depth
```

---

## 6. Authentication & Authorization

### OAuth 2.0 Flow (NextAuth.js)

```typescript
// frontend/lib/auth.ts
import NextAuth from "next-auth"
import GoogleProvider from "next-auth/providers/google"

export const authOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          hd: "stanford.edu", // Restrict to Stanford domain
          prompt: "select_account"
        }
      }
    })
  ],

  callbacks: {
    async signIn({ user, account, profile }) {
      // Verify user is in database
      const response = await fetch(`${API_URL}/api/v1/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user.email })
      })

      const { is_authorized } = await response.json()
      return is_authorized
    },

    async jwt({ token, account }) {
      // Add access token to JWT
      if (account) {
        token.accessToken = account.access_token
      }
      return token
    },

    async session({ session, token }) {
      // Fetch user role from API
      const response = await fetch(`${API_URL}/api/v1/users/me`, {
        headers: { Authorization: `Bearer ${token.accessToken}` }
      })
      const user = await response.json()

      session.user.id = user.id
      session.user.role = user.role
      return session
    }
  },

  pages: {
    signIn: '/login',
    error: '/auth/error'
  }
}

export default NextAuth(authOptions)
```

### Backend JWT Verification

```python
# backend/app/middleware/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from google.oauth2 import id_token
from google.auth.transport import requests

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify Google OAuth token and return user.
    """
    token = credentials.credentials

    try:
        # Verify Google ID token
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Check domain
        if idinfo.get("hd") != "stanford.edu":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only stanford.edu accounts allowed"
            )

        email = idinfo["email"]

        # Fetch user from database
        result = await db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized"
            )

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        return user

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

# Role-based access control
def require_role(*allowed_roles: str):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker

# Usage in endpoints
@router.delete("/api/v1/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    # Only admins can delete users
    ...
```

---

## 7. Deployment & CI/CD

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

env:
  GCP_PROJECT_ID: slr-production
  GCP_REGION: us-west1

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy-backend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Build and push Docker image
        run: |
          cd backend
          gcloud builds submit \
            --tag gcr.io/$GCP_PROJECT_ID/slr-api:${{ github.sha }} \
            --tag gcr.io/$GCP_PROJECT_ID/slr-api:latest

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy slr-api \
            --image gcr.io/$GCP_PROJECT_ID/slr-api:${{ github.sha }} \
            --region $GCP_REGION \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars="ENVIRONMENT=production" \
            --set-secrets="DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-key:latest"

      - name: Run database migrations
        run: |
          # Connect to Cloud SQL via proxy and run migrations
          gcloud sql connect slr-db --user=postgres < backend/alembic/versions/*.sql

  deploy-functions:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    strategy:
      matrix:
        function: [sp_machine, r1_machine, r2_pipeline]

    steps:
      - uses: actions/checkout@v3

      - name: Deploy ${{ matrix.function }}
        run: |
          gcloud functions deploy ${{ matrix.function }} \
            --gen2 \
            --runtime python311 \
            --region $GCP_REGION \
            --source functions/${{ matrix.function }} \
            --entry-point handle_${{ matrix.function }}_queue \
            --trigger-topic ${{ matrix.function }}-queue \
            --set-secrets="DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-key:latest" \
            --memory 512MB \
            --timeout 540s

  deploy-frontend:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      # Vercel automatically deploys on push to main
      # Just need to set environment variables in Vercel dashboard
      - name: Deploy to Vercel
        run: echo "Vercel auto-deploys from GitHub. Check dashboard."
```

### Vercel Configuration

```json
// vercel.json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://slr-api-xxxxx-uw.a.run.app",
    "GOOGLE_CLIENT_ID": "@google-oauth-client-id",
    "GOOGLE_CLIENT_SECRET": "@google-oauth-client-secret",
    "NEXTAUTH_URL": "https://slr.stanford.edu",
    "NEXTAUTH_SECRET": "@nextauth-secret"
  },
  "regions": ["sfo1"],
  "github": {
    "enabled": true,
    "autoJobCancelation": true,
    "silent": false
  }
}
```

---

## 8. Cost Breakdown (Monthly Estimates)

### Development/Staging Environment
```
Cloud SQL (db-f1-micro):        $7
Cloud Run API:                  $0  (within free tier)
Cloud Functions:                $0  (within free tier)
Cloud Storage:                  $1  (20 GB @ $0.02/GB)
Pub/Sub:                        $0  (within free tier)
Cloud Logging (50 GB):          $0  (first 50 GB free)
Vercel:                         $0  (free tier)
OpenAI API (dev testing):       $5  (light usage)
--------------------------------------------
TOTAL:                          $13/month
```

### Production Environment
```
Cloud SQL (db-g1-small):        $25
Cloud Run API:                  $5   (~50k requests/month)
Cloud Functions (3 stages):     $3   (~5k invocations/month)
Cloud Storage:                  $10  (500 GB @ $0.02/GB + egress)
Pub/Sub:                        $1
Cloud Monitoring:               $0   (within free tier)
Cloud Logging (200 GB):         $10  ($0.50/GB after 50 GB)
Sentry (Team plan):             $0   (100k events/month free)
Vercel:                         $0   (free for open source/education)
OpenAI API (production):        $50  (GPT-4o-mini, ~10k citations/month)
--------------------------------------------
TOTAL:                          $104/month

With High Availability SQL:     +$50
With reserved Cloud Run:        +$10
--------------------------------------------
PRODUCTION HA TOTAL:            $164/month
```

### Cost Optimization Strategies
1. **Use GPT-4o-mini** instead of GPT-4 (10x cheaper)
2. **Batch citations** to reduce function invocations
3. **Cache LLM responses** for similar citations
4. **Scale Cloud SQL to zero** during off-hours (custom script)
5. **Use Cloud Storage lifecycle policies** to archive old PDFs to Coldline

---

## 9. Security Considerations

### Data Protection
```
✓ All data encrypted at rest (Cloud SQL, Cloud Storage)
✓ TLS 1.3 for all data in transit
✓ Private IP for Cloud SQL (not public)
✓ VPC connector for Cloud Run → Cloud SQL
✓ Secrets stored in Google Secret Manager (never in code)
✓ IAM roles follow principle of least privilege
✓ Service accounts for each component
```

### Compliance
```
✓ FERPA compliant (educational records)
✓ Data residency: all in US (us-west1)
✓ Audit logging enabled (90-day retention)
✓ Regular automated backups (7-day retention)
✓ No PII stored except email (required for auth)
```

### Application Security
```
✓ CORS configured for Vercel origin only
✓ Rate limiting (100 req/min per user)
✓ SQL injection protection (parameterized queries via SQLAlchemy)
✓ XSS protection (React escapes by default)
✓ CSRF protection (SameSite cookies)
✓ Content Security Policy headers
✓ Dependency scanning (Dependabot + Snyk)
```

---

## 10. Migration Strategy from Google Sheets

### Phase 1: Data Export (Week 1)
```python
# scripts/export_sheets_to_sql.py
import gspread
from sqlalchemy import create_engine
from models import User, Task, TaskAssignment

# Connect to Google Sheets
gc = gspread.service_account()
sheet = gc.open("78.6 Sanders Master Sheet")

# Export Members tab
members_ws = sheet.worksheet("Members")
members_data = members_ws.get_all_records()

engine = create_engine(DATABASE_URL)
with engine.begin() as conn:
    for row in members_data:
        user = User(
            id=row["member_id"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"]
        )
        conn.add(user)

    # Export Tasks, Assignments, etc.
    ...
```

### Phase 2: Parallel Run (Weeks 2-3)
- Keep Google Sheets as read-only archive
- New data goes to PostgreSQL
- Compare outputs for validation

### Phase 3: Cutover (Week 4)
- Archive Google Sheets
- Full production on new stack

---

## 11. Testing Strategy

```
Unit Tests:
✓ Backend API endpoints (pytest + httpx)
✓ Database models and queries
✓ Citation validation logic
✓ PDF processing functions

Integration Tests:
✓ End-to-end API workflows
✓ Database transactions
✓ Pub/Sub message handling
✓ Cloud Storage operations

E2E Tests:
✓ Frontend user flows (Playwright)
✓ Full pipeline (submit article → R2 complete)

Performance Tests:
✓ Load testing API (Locust)
✓ Database query performance
✓ Concurrent user simulation

Target Coverage: 80% for critical paths
```

---

## Summary: Why This Architecture?

| Requirement | Solution | Benefit |
|-------------|----------|---------|
| **Scalability** | Cloud Run + Cloud SQL | Auto-scales 0→1000 users |
| **Reliability** | Pub/Sub + retries + DLQ | Automatic failure recovery |
| **Performance** | PostgreSQL + indexes | Fast queries (ms not seconds) |
| **Cost** | Free tiers + serverless | $50-100/month all-in |
| **Developer Experience** | Modern stack + TypeScript | Fast iteration |
| **Observability** | Cloud Monitoring + Sentry | Find issues before users do |
| **Security** | OAuth + IAM + encryption | Enterprise-grade |
| **Free Frontend** | Vercel | $0 for hosting |

**This is production-ready architecture** that will scale from 10 to 1000 users without major changes.
