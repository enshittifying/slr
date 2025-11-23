# Stanford Law Review Citation System

**Production-grade automated citation checking system for legal academic publishing.**

🚀 **Status:** MVP Backend Complete | Frontend & Pipeline In Progress

---

## 📋 Table of Contents

- [Overview](#overview)
- [What's Been Built](#whats-been-built)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Development](#development)
- [What's Next](#whats-next)
- [Contributing](#contributing)

---

## Overview

This system automates the citation checking process for the Stanford Law Review through a three-stage pipeline:

1. **Stage 1 (sp_machine)**: Retrieve PDFs from legal databases
2. **Stage 2 (R1 Machine)**: Prepare PDFs and extract metadata via OCR/NLP
3. **Stage 3 (r2_pipeline)**: Validate citations using LLM (GPT-4o-mini)

### Technology Stack

- **Backend**: FastAPI (Python 3.11) + PostgreSQL + SQLAlchemy 2.0
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS *(in progress)*
- **Pipeline**: Google Cloud Functions + Pub/Sub *(planned)*
- **Deployment**: Cloud Run (backend) + Vercel (frontend) + Cloud SQL
- **Auth**: Google OAuth 2.0 with stanford.edu domain restriction

---

## What's Been Built

### ✅ Complete

#### Backend Infrastructure
- [x] FastAPI application with async/await support
- [x] PostgreSQL database models (SQLAlchemy 2.0)
- [x] Alembic migrations setup with initial schema
- [x] Docker Compose for local development
- [x] Google OAuth authentication middleware
- [x] CORS and security configuration

#### Database Schema
- [x] Users table with role-based access
- [x] Tasks and task assignments
- [x] Articles and citations
- [x] Forms and form submissions
- [x] Events and attendance tracking
- [x] System config and audit logs
- [x] All indexes and foreign keys

#### API Endpoints (Core)
- [x] `/api/v1/users` - User management (CRUD)
- [x] `/api/v1/articles` - Article management with statistics
- [x] `/api/v1/citations` - Citation management
- [x] `/health` - Health check
- [x] `/docs` - Auto-generated Swagger docs

#### Pydantic Schemas
- [x] Complete request/response schemas for all models
- [x] Validation rules and type safety
- [x] Pagination and error response schemas

#### DevOps
- [x] Dockerfile (multi-stage build for production)
- [x] Docker Compose (db, redis, backend, frontend)
- [x] Database seed script with test data

#### Documentation
- [x] Production Architecture document (13K words)
- [x] API Specification (complete endpoint documentation)
- [x] Development Setup Guide (comprehensive)
- [x] This README

### ⏳ In Progress / Planned

#### Backend API (Remaining Endpoints)
- [ ] `/api/v1/tasks` - Task management
- [ ] `/api/v1/forms` - Dynamic form system
- [ ] `/api/v1/events` - Event and attendance
- [ ] `/api/v1/auth` - Auth verification endpoint
- [ ] `/api/v1/pipeline` - Pipeline job management

#### Frontend (Next.js)
- [ ] Project setup with TypeScript
- [ ] NextAuth.js Google OAuth integration
- [ ] Dashboard layout and navigation
- [ ] User management UI
- [ ] Article and citation management UI
- [ ] Task dashboard
- [ ] Forms builder
- [ ] Real-time updates (WebSockets or polling)

#### Pipeline (Cloud Functions)
- [ ] `sp_machine` - Stage 1: Sourcepull
- [ ] `r1_machine` - Stage 2: PDF preparation & metadata extraction
- [ ] `r2_pipeline` - Stage 3: LLM validation
- [ ] Pub/Sub integration for orchestration
- [ ] Cloud Storage setup for PDFs

#### Testing
- [ ] Backend unit tests (pytest)
- [ ] API integration tests
- [ ] Frontend tests (Jest + Playwright)
- [ ] End-to-end pipeline tests

#### CI/CD
- [ ] GitHub Actions workflows
- [ ] Automated testing on PR
- [ ] Deployment to Cloud Run
- [ ] Database migration automation

---

## Getting Started

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (if running locally without Docker)
- **Node.js 18+** (for frontend)
- **PostgreSQL 15+** (if running locally without Docker)
- **Google Cloud account** (for production deployment)
- **OpenAI API key**

### Quick Start (Docker)

1. **Clone the repository:**
   ```bash
   git checkout claude/explore-repo-setup-011CV4T6t2vUBz4WwAMCUNWF
   cd slr
   ```

2. **Copy environment files:**
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   # Edit .env files with your credentials
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations and seed data:**
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python scripts/seed_database.py
   ```

5. **Access the API:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:3000 *(when implemented)*

### Test Users

After seeding, you can test with these accounts (all @stanford.edu):

| Role | Email | Purpose |
|------|-------|---------|
| Admin | admin@stanford.edu | Full system access |
| Senior Editor | senior@stanford.edu | Manage articles and assignments |
| Member Editor 1 | member1@stanford.edu | Regular editor |
| Member Editor 2 | member2@stanford.edu | Regular editor |

**Note:** In development mode, OAuth domain restriction is relaxed. In production, only @stanford.edu emails are allowed.

---

## Architecture

### System Layers

```
┌──────────────────────────────────────┐
│  Frontend (Vercel)                   │
│  Next.js + React + Tailwind          │
└────────────┬─────────────────────────┘
             │ HTTPS (OAuth + JWT)
┌────────────▼─────────────────────────┐
│  Backend API (Cloud Run)             │
│  FastAPI + SQLAlchemy                │
└────────────┬─────────────────────────┘
             │ Connection Pool
┌────────────▼─────────────────────────┐
│  Database (Cloud SQL)                │
│  PostgreSQL 15                       │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  Pipeline (Cloud Functions)          │
│  sp → r1 → r2 (via Pub/Sub)         │
└──────────────────────────────────────┘
```

### Data Model

**Core Entities:**
- **Users**: Member editors with role-based permissions
- **Articles**: Submitted papers with volume/issue tracking
- **Citations**: Individual citations with 3-stage pipeline status
- **Tasks**: Assignments for editors with status tracking
- **Forms**: Dynamic forms for data collection
- **Events**: Calendar events with attendance tracking

**Key Relationships:**
- Articles have many Citations
- Tasks have many TaskAssignments (many-to-many with Users)
- Events have many AttendanceRecords

See `info/Production_Architecture.md` for complete schema details.

---

## API Documentation

### Authentication

All API endpoints (except `/health` and `/`) require Google OAuth Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_GOOGLE_ID_TOKEN" \
     http://localhost:8000/api/v1/users/me
```

### Core Endpoints

#### Users

```bash
# Get current user
GET /api/v1/users/me

# List users (paginated)
GET /api/v1/users?page=1&per_page=50&role=member_editor

# Create user (admin only)
POST /api/v1/users
{
  "email": "newuser@stanford.edu",
  "full_name": "New User",
  "role": "member_editor"
}

# Update user
PATCH /api/v1/users/{user_id}

# Delete user (soft delete, admin only)
DELETE /api/v1/users/{user_id}
```

#### Articles

```bash
# List articles
GET /api/v1/articles?status=r2_in_progress&volume_number=79

# Get article with citation stats
GET /api/v1/articles/{article_id}

# Create article
POST /api/v1/articles
{
  "title": "Article Title",
  "author_name": "Author Name",
  "volume_number": 79,
  "issue_number": 1,
  "assigned_editor": "uuid-here"
}

# Update article
PATCH /api/v1/articles/{article_id}
```

#### Citations

```bash
# List citations
GET /api/v1/citations?article_id={uuid}&requires_manual_review=true

# Get citation details
GET /api/v1/citations/{citation_id}

# Create citation
POST /api/v1/citations
{
  "article_id": "uuid-here",
  "footnote_number": 1,
  "citation_text": "Doe v. Roe, 123 U.S. 456 (1990).",
  "proposition": "This case establishes...",
  "source_type": "case"
}

# Update citation
PATCH /api/v1/citations/{citation_id}
```

### Full API Spec

See `info/API_Specification.md` for complete endpoint documentation including:
- Request/response schemas
- Error codes
- Rate limiting
- Pagination
- WebSocket API (planned)

---

## Development

### Project Structure

```
slr/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   │   ├── deps.py     # Auth dependencies
│   │   │   └── v1/         # API v1 routes
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── config.py       # App configuration
│   │   ├── database.py     # DB connection
│   │   └── main.py         # FastAPI app
│   ├── alembic/            # Database migrations
│   ├── scripts/            # Utility scripts
│   ├── tests/              # Tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend (planned)
├── functions/              # Cloud Functions (planned)
│   ├── sp_machine/
│   ├── r1_machine/
│   └── r2_pipeline/
├── reference_files/        # Bluebook/Redbook rules
├── info/                   # Documentation
└── docker-compose.yml
```

### Running Locally (Without Docker)

**Backend:**
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Start PostgreSQL (Docker or local)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15

# Run migrations
alembic upgrade head

# Seed database
python scripts/seed_database.py

# Start server
uvicorn app.main:app --reload
```

**Frontend:** *(when implemented)*
```bash
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
# Create new migration (auto-generate from model changes)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback all
alembic downgrade base
```

### Code Quality

```bash
# Format code
black backend/app
isort backend/app

# Lint
flake8 backend/app

# Type check
mypy backend/app

# Run tests
pytest backend/tests --cov=app
```

---

## Deployment

### Backend (Cloud Run)

```bash
cd backend

# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/slr-api:latest

# Deploy
gcloud run deploy slr-api \
  --image gcr.io/PROJECT_ID/slr-api:latest \
  --region us-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-key:latest"
```

### Frontend (Vercel)

```bash
cd frontend
vercel --prod
```

See `info/Development_Setup.md` for complete deployment instructions.

---

## What's Next

### Immediate Priorities

1. **Complete Backend API** (1-2 weeks)
   - Tasks endpoints
   - Forms endpoints
   - Events endpoints
   - Pipeline management endpoints

2. **Build Frontend** (2-3 weeks)
   - NextAuth setup
   - Dashboard UI
   - Article/citation management
   - Task management

3. **Implement Pipeline** (2-3 weeks)
   - Stage 1: PDF retrieval
   - Stage 2: OCR & metadata extraction
   - Stage 3: LLM validation
   - Pub/Sub orchestration

4. **Testing & CI/CD** (1 week)
   - Unit tests
   - Integration tests
   - GitHub Actions workflows

### Feature Roadmap

**Phase 1 (MVP)** - Current
- ✅ Core database and API
- ⏳ Basic frontend
- ⏳ Pipeline prototype

**Phase 2** - Q1 2026
- [ ] WebSocket real-time updates
- [ ] Advanced search and filtering
- [ ] Export to Word/PDF
- [ ] Email notifications

**Phase 3** - Q2 2026
- [ ] ML-powered citation parsing
- [ ] Integration with Westlaw/Lexis APIs
- [ ] Mobile-responsive design
- [ ] Analytics dashboard

---

## Cost Estimates

### Development Environment
- Cloud SQL (db-f1-micro): $7/month
- Cloud Run: $0 (free tier)
- Cloud Functions: $0 (free tier)
- Cloud Storage: $1/month
- Vercel: $0 (free tier)
**Total: ~$10/month**

### Production Environment
- Cloud SQL (db-g1-small): $25/month
- Cloud Run API: $5/month
- Cloud Functions (3 stages): $3/month
- Cloud Storage: $10/month
- OpenAI API (GPT-4o-mini): $50/month
- Monitoring & Logging: $10/month
- Vercel: $0 (free for open source/education)
**Total: ~$100/month**

See `info/Production_Architecture.md` for detailed cost breakdown.

---

## Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/name`
2. Make changes
3. Run tests: `pytest`
4. Lint: `black . && flake8 .`
5. Commit: `git commit -m "feat: description"`
6. Push: `git push origin feature/name`
7. Create Pull Request

### Commit Convention

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Build/tooling

---

## License

MIT License - Copyright (c) 2025

---

## Support

- **Documentation**: `info/` directory
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: GitHub Issues
- **Architecture**: See `info/Production_Architecture.md`
- **Setup Guide**: See `info/Development_Setup.md`

---

## Quick Commands Reference

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed database
docker-compose exec backend python scripts/seed_database.py

# Run tests
docker-compose exec backend pytest

# Shell into backend
docker-compose exec backend bash

# Stop everything
docker-compose down

# Reset database (⚠️ destroys data)
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/seed_database.py
```

---

**Built with ❤️ for Stanford Law Review**

*For questions or issues, please refer to the documentation in the `info/` directory.*
