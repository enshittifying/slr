# Development Setup Guide

Complete guide to setting up the Stanford Law Review Citation System for local development.

---

## Prerequisites

### Required Software
- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 15+
- **Docker** & Docker Compose (recommended for local dev)
- **Google Cloud SDK** (`gcloud` CLI)
- **Git**

### Required Accounts
- Google Cloud Project (with billing enabled)
- Vercel account (free tier OK)
- OpenAI API key
- Sentry account (optional, free tier available)

---

## Project Structure

```
slr/
├── frontend/                    # Next.js frontend
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── backend/                     # FastAPI backend
│   ├── app/
│   ├── alembic/                # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── functions/                   # Cloud Functions (pipeline stages)
│   ├── sp_machine/
│   ├── r1_machine/
│   └── r2_pipeline/
├── reference_files/            # Bluebook/Redbook rules
│   ├── Bluebook.json
│   └── redbook_processed/
├── scripts/                    # Utility scripts
│   ├── export_sheets_to_sql.py
│   └── seed_database.py
├── docs/                       # Additional documentation
├── .github/
│   └── workflows/              # CI/CD pipelines
├── docker-compose.yml
└── README.md
```

---

## 1. Local Development with Docker Compose

### Step 1: Clone the Repository

```bash
git clone https://github.com/stanford-law-review/slr-citation-system.git
cd slr-citation-system
```

### Step 2: Create Environment Files

**`.env` (root directory):**
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/slr_dev

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# OpenAI
OPENAI_API_KEY=sk-...

# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=generate_with_openssl_rand_base64_32

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Sentry (optional)
SENTRY_DSN=https://...

# Environment
ENVIRONMENT=development
```

**`backend/.env`:**
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/slr_dev
OPENAI_API_KEY=sk-...
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000
```

**`frontend/.env.local`:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_secret_here
```

### Step 3: Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs:
   - `http://localhost:3000/api/auth/callback/google` (dev)
   - `https://your-vercel-app.vercel.app/api/auth/callback/google` (prod)
7. Copy Client ID and Client Secret to `.env` files

### Step 4: Start Services with Docker Compose

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: slr-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: slr_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: slr-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: slr-backend
    env_file:
      - backend/.env
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - /app/.venv  # Don't mount virtualenv
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: slr-frontend
    env_file:
      - frontend/.env.local
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    depends_on:
      - backend
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
```

**Start everything:**
```bash
docker-compose up -d
```

**Check logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Step 5: Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed with test data
docker-compose exec backend python scripts/seed_database.py
```

### Step 6: Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Database:** localhost:5432

---

## 2. Manual Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing

# Create .env file (see above)
cp .env.example .env
# Edit .env with your credentials

# Run PostgreSQL locally or use Docker
docker run -d \
  --name slr-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=slr_dev \
  -p 5432:5432 \
  postgres:15-alpine

# Run migrations
alembic upgrade head

# Seed database
python scripts/seed_database.py

# Start backend
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local (see above)
cp .env.example .env.local
# Edit .env.local with your credentials

# Start dev server
npm run dev
```

---

## 3. Database Migrations

### Create a New Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add citation validation fields"

# Review generated migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all
alembic downgrade base
```

### Reset Database (Development Only)

```bash
# Drop all tables and recreate
alembic downgrade base
alembic upgrade head
python scripts/seed_database.py
```

---

## 4. Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_citations.py

# Run specific test
pytest tests/test_api/test_citations.py::test_create_citation

# Run with verbose output
pytest -v

# Open coverage report
open htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests (Playwright)
npm run test:e2e

# Run E2E in UI mode
npm run test:e2e:ui

# Generate test coverage
npm run test:coverage
```

---

## 5. Cloud Functions Local Development

### Install Functions Framework

```bash
pip install functions-framework
```

### Run Stage 1 (sp_machine) Locally

```bash
cd functions/sp_machine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/slr_dev
export OPENAI_API_KEY=sk-...

# Start function
functions-framework --target=handle_sp_queue --debug --port=8001
```

### Test Function with Local Pub/Sub Emulator

```bash
# Install Pub/Sub emulator
gcloud components install pubsub-emulator

# Start emulator
gcloud beta emulators pubsub start --project=test-project

# In another terminal, set environment
$(gcloud beta emulators pubsub env-init)

# Publish test message
python scripts/test_pubsub.py
```

---

## 6. Google Cloud Setup

### Install and Configure gcloud CLI

```bash
# Install gcloud SDK
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Initialize
gcloud init

# Login
gcloud auth login

# Set project
gcloud config set project slr-production
```

### Create Cloud SQL Instance (Development)

```bash
# Create db-f1-micro instance
gcloud sql instances create slr-db-dev \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-west1 \
  --root-password=choose_secure_password

# Create database
gcloud sql databases create slr_dev --instance=slr-db-dev

# Get connection name
gcloud sql instances describe slr-db-dev --format="value(connectionName)"
# Output: project-id:us-west1:slr-db-dev
```

### Connect to Cloud SQL Locally

```bash
# Install Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Start proxy
./cloud-sql-proxy project-id:us-west1:slr-db-dev
# Now connect via localhost:5432
```

### Create Cloud Storage Buckets

```bash
# Create buckets
gcloud storage buckets create gs://slr-pdfs-dev \
  --location=us-west1 \
  --uniform-bucket-level-access

# Set lifecycle policy (archive old PDFs)
gcloud storage buckets update gs://slr-pdfs-dev \
  --lifecycle-file=storage-lifecycle.json
```

**`storage-lifecycle.json`:**
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 180}
      }
    ]
  }
}
```

### Create Pub/Sub Topics

```bash
gcloud pubsub topics create sp-queue
gcloud pubsub topics create r1-queue
gcloud pubsub topics create r2-queue
gcloud pubsub topics create dlq-queue

# Create subscriptions
gcloud pubsub subscriptions create sp-queue-sub \
  --topic=sp-queue \
  --ack-deadline=600 \
  --max-delivery-attempts=5 \
  --dead-letter-topic=dlq-queue
```

---

## 7. Deployment

### Deploy Backend to Cloud Run

```bash
cd backend

# Build and push image
gcloud builds submit --tag gcr.io/slr-production/slr-api:latest

# Deploy to Cloud Run
gcloud run deploy slr-api \
  --image gcr.io/slr-production/slr-api:latest \
  --platform managed \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production" \
  --set-secrets="DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-key:latest" \
  --min-instances=0 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1

# Get URL
gcloud run services describe slr-api --region us-west1 --format="value(status.url)"
```

### Deploy Cloud Functions

```bash
cd functions/sp_machine

gcloud functions deploy sp-machine \
  --gen2 \
  --runtime=python311 \
  --region=us-west1 \
  --source=. \
  --entry-point=handle_sp_queue \
  --trigger-topic=sp-queue \
  --set-secrets="DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-key:latest" \
  --memory=512MB \
  --timeout=540s

# Repeat for r1_machine and r2_pipeline
```

### Deploy Frontend to Vercel

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy (first time)
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: slr-frontend
# - Directory: ./
# - Override settings? No

# Set environment variables in Vercel dashboard
# Or via CLI:
vercel env add NEXT_PUBLIC_API_URL
# Paste: https://slr-api-xxxxx-uw.a.run.app

# Deploy to production
vercel --prod
```

---

## 8. Secrets Management

### Store Secrets in Google Secret Manager

```bash
# Create secrets
echo -n "postgresql://user:pass@host/db" | \
  gcloud secrets create database-url --data-file=-

echo -n "sk-..." | \
  gcloud secrets create openai-key --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding database-url \
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# List secrets
gcloud secrets list
```

### Access Secrets Locally

```bash
# Get secret value
gcloud secrets versions access latest --secret=database-url
```

---

## 9. Monitoring & Debugging

### View Cloud Run Logs

```bash
# Stream logs
gcloud run logs tail slr-api --region us-west1

# Filter by severity
gcloud run logs read slr-api --region us-west1 --filter="severity>=ERROR"
```

### View Cloud Function Logs

```bash
gcloud functions logs read sp-machine --region us-west1
```

### Access Cloud SQL from Local Machine

```bash
# Start Cloud SQL Proxy
./cloud-sql-proxy project-id:us-west1:slr-db

# Connect with psql
psql "host=127.0.0.1 port=5432 dbname=slr_dev user=postgres"
```

### Debug with Cloud SQL Studio

```bash
# Open Cloud Console
gcloud console sql instances describe slr-db --region us-west1

# Click "Connect using Cloud Shell"
```

---

## 10. Code Quality Tools

### Backend Linting & Formatting

```bash
cd backend

# Install dev tools
pip install black isort flake8 mypy

# Format code
black app/
isort app/

# Lint
flake8 app/

# Type checking
mypy app/
```

**`.flake8`:**
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,.venv,alembic
ignore = E203,W503
```

**`pyproject.toml`:**
```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100
```

### Frontend Linting & Formatting

```bash
cd frontend

# Lint
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Format with Prettier
npm run format

# Type check
npm run type-check
```

**`.eslintrc.json`:**
```json
{
  "extends": ["next/core-web-vitals", "prettier"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn"
  }
}
```

---

## 11. Useful Scripts

### Seed Database with Test Data

**`scripts/seed_database.py`:**
```python
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User, Article, Citation

async def seed():
    async with AsyncSessionLocal() as db:
        # Create admin user
        admin = User(
            email="admin@stanford.edu",
            full_name="Admin User",
            role="admin"
        )
        db.add(admin)

        # Create test article
        article = Article(
            title="Test Article",
            author_name="Test Author",
            volume_number=79,
            issue_number=1,
            assigned_editor=admin.id
        )
        db.add(article)
        await db.commit()

        # Create test citations
        for i in range(10):
            citation = Citation(
                article_id=article.id,
                footnote_number=i + 1,
                citation_text=f"Test Citation {i+1}",
                proposition=f"Test proposition {i+1}",
                source_type="case"
            )
            db.add(citation)

        await db.commit()
        print("✓ Database seeded successfully")

if __name__ == "__main__":
    asyncio.run(seed())
```

### Export Google Sheets to PostgreSQL

**`scripts/export_sheets_to_sql.py`:**
```python
import gspread
from sqlalchemy import create_engine
from app.models import User, Task
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

gc = gspread.service_account(filename="credentials.json")
sheet = gc.open("78.6 Sanders Master Sheet")

members_ws = sheet.worksheet("Members")
members_data = members_ws.get_all_records()

with engine.begin() as conn:
    for row in members_data:
        user = User(
            id=row["member_id"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"]
        )
        conn.add(user)

print("Migration complete!")
```

---

## 12. Common Issues & Solutions

### Issue: Database connection refused

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart database
docker-compose restart db

# Check connection
psql postgresql://postgres:postgres@localhost:5432/slr_dev
```

### Issue: Frontend can't connect to backend

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/api/v1/health

# Check CORS settings in backend/app/main.py
# Ensure NEXT_PUBLIC_API_URL is set correctly in frontend/.env.local
```

### Issue: OAuth login fails

**Solution:**
1. Verify Google OAuth credentials are correct
2. Check redirect URI matches exactly (including protocol)
3. Ensure `hd=stanford.edu` parameter is set
4. Check NEXTAUTH_SECRET is set

### Issue: Cloud Function timeout

**Solution:**
```bash
# Increase timeout (max 540s)
gcloud functions deploy sp-machine --timeout=540s

# Check function logs for specific error
gcloud functions logs read sp-machine --limit=50
```

### Issue: Alembic migration conflict

**Solution:**
```bash
# Merge heads if multiple branches
alembic merge heads -m "merge migrations"

# Or reset and recreate
alembic downgrade base
alembic upgrade head
```

---

## 13. Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/citation-comments

# 2. Make changes
# Edit code...

# 3. Run tests
pytest  # backend
npm test  # frontend

# 4. Lint and format
black app/
npm run lint:fix

# 5. Commit
git add .
git commit -m "feat: add citation comments feature"

# 6. Push and create PR
git push origin feature/citation-comments
```

### Database Schema Changes

```bash
# 1. Update models in backend/app/models/
# 2. Generate migration
alembic revision --autogenerate -m "add citation comments table"

# 3. Review migration file
# 4. Test migration
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# 5. Commit migration
git add alembic/versions/*.py
git commit -m "db: add citation comments table"
```

---

## 14. Performance Tips

### Backend Optimization

```python
# Use async/await everywhere
async def get_citations(db: AsyncSession, article_id: str):
    result = await db.execute(
        select(Citation).where(Citation.article_id == article_id)
    )
    return result.scalars().all()

# Use eager loading to avoid N+1 queries
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Article).options(
        selectinload(Article.citations),
        selectinload(Article.assigned_editor)
    )
)

# Use indexes
# Already defined in schema, but verify:
# CREATE INDEX idx_citations_article ON citations(article_id);
```

### Frontend Optimization

```typescript
// Use React Query for caching
const { data, isLoading } = useQuery({
  queryKey: ['citations', articleId],
  queryFn: () => api.getCitations(articleId),
  staleTime: 5 * 60 * 1000  // 5 minutes
})

// Use dynamic imports for large components
const CitationEditor = dynamic(() => import('./CitationEditor'), {
  loading: () => <Spinner />
})

// Optimize images
import Image from 'next/image'
<Image src="/logo.png" width={200} height={50} alt="Logo" />
```

---

## 15. Useful Commands Cheat Sheet

```bash
# Docker
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f backend    # Follow backend logs
docker-compose exec backend bash  # Shell into backend container

# Backend
uvicorn app.main:app --reload     # Start dev server
pytest                            # Run tests
alembic upgrade head              # Run migrations
black app/ && isort app/          # Format code

# Frontend
npm run dev                       # Start dev server
npm test                          # Run tests
npm run lint                      # Lint code
npm run build                     # Production build

# Google Cloud
gcloud auth login                             # Login
gcloud config set project PROJECT_ID          # Set project
gcloud sql connect slr-db --user=postgres     # Connect to Cloud SQL
gcloud run logs tail slr-api                  # Tail logs
gcloud secrets versions access latest --secret=NAME  # Get secret

# Git
git checkout -b feature/name      # Create feature branch
git add .                         # Stage changes
git commit -m "feat: description" # Commit
git push origin feature/name      # Push branch
```

---

## Next Steps

1. ✅ Complete this setup guide
2. ✅ Run the application locally
3. ⬜ Review the codebase structure
4. ⬜ Make a small change and test it
5. ⬜ Deploy to staging environment
6. ⬜ Set up monitoring and alerts
7. ⬜ Start building features!

---

## Getting Help

- **Documentation:** `/docs` directory
- **API Docs:** http://localhost:8000/docs (when running)
- **Issues:** GitHub Issues
- **Team Chat:** Slack #slr-dev

**Happy coding! 🚀**
