# Stanford Law Review Workflow Management System

A comprehensive workflow management system for the Stanford Law Review, featuring a Flask web application and a three-stage automated editorial pipeline with LLM-powered validation.

## System Architecture

**Tech Stack:** Python + Flask + PostgreSQL + Vercel

The system has been redesigned from Google Apps Script to a proper web application architecture to support concurrent users and scalability.

### Components

1. **Flask Web Application**: Modern web app for task management, attendance tracking, and form handling
2. **PostgreSQL Database**: Robust relational database with proper transaction support and concurrency control
3. **sp_machine (Sourcepull Machine)**: Retrieves raw, format-preserving source files based on citations
4. **r1_machine (Preparation Machine)**: Prepares sources for review by cleaning PDFs and performing metadata redboxing
5. **r2_machine (Validation Machine)**: Performs LLM-powered validation including Bluebook checking and proposition support verification

**Why Not Google Apps Script?**
- ❌ Concurrency issues with LockService
- ❌ 6-minute execution time limit
- ❌ Limited debugging and testing capabilities
- ✅ Flask + PostgreSQL provides proper concurrent user support and scalability

## Project Structure

```
slr/
├── api/                     # Vercel serverless function entry point
│   └── index.py
├── web_app/                 # Main Flask application
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration management
│   ├── models/              # SQLAlchemy database models
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── form.py
│   │   ├── attendance.py
│   │   └── config.py
│   ├── routes/              # API endpoints and views
│   │   ├── auth.py          # Google OAuth authentication
│   │   ├── dashboard.py     # Main UI routes
│   │   ├── tasks.py         # Task management
│   │   ├── forms.py         # Form handling
│   │   ├── attendance.py    # Attendance tracking
│   │   └── api.py           # REST API
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JavaScript, images
├── sp_machine/              # Stage 1: Source retrieval
│   ├── main.py
│   └── src/
├── r1_machine/              # Stage 2: PDF preparation & redboxing
│   ├── main.py
│   └── src/
├── r2_machine/              # Stage 3: LLM-powered validation
│   ├── main.py
│   ├── src/
│   └── prompts/
├── shared_utils/            # Shared utilities across machines
│   ├── config.py
│   ├── google_auth.py
│   ├── logger.py
│   └── exceptions.py
├── migrations/              # Alembic database migrations
├── tests/                   # Unit and integration tests
├── docs/                    # Documentation
│   ├── REVISED_ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── scripts/                 # Utility scripts
│   └── init_db.py           # Database initialization
├── vercel.json              # Vercel deployment config
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variables template
```

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Google Cloud Project (for OAuth and APIs)
- Vercel account (for deployment)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/enshittifying/slr.git
   cd slr
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database:**
   ```bash
   # Create database
   createdb slr_db

   # Initialize tables
   python scripts/init_db.py --seed
   ```

6. **Run development server:**
   ```bash
   export FLASK_APP=api/index.py
   export FLASK_ENV=development
   flask run
   ```

7. **Access the application:**
   - Open http://localhost:5000
   - Sign in with your @stanford.edu Google account

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=web_app --cov=shared_utils

# Run specific test file
pytest tests/unit/test_models.py
```

## Deployment

### Deploy to Vercel

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

**Quick deploy:**

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

**Required Environment Variables:**
- `SECRET_KEY` - Flask secret key
- `POSTGRES_URL` - PostgreSQL connection string
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key

## Usage

### Web Application

**For Members:**
- View assigned tasks
- Update task status
- Submit forms
- Log attendance

**For Senior Editors:**
- Create and assign tasks
- Manage forms
- View attendance reports
- Monitor member progress

**For Admins:**
- All senior editor permissions
- User management
- System configuration

### Running the Pipeline

Each article goes through the three-stage pipeline:

```bash
# Stage 1: Retrieve sources
cd sp_machine
python main.py --article-id "79.1.article_name"

# Stage 2: Prepare PDFs
cd ../r1_machine
python main.py --input ../sp_machine/output --article-id "79.1.article_name"

# Stage 3: Validate citations
cd ../r2_machine
python main.py --input ../r1_machine/output --article-id "79.1.article_name"
```

## Database Schema

**Core Tables:**
- `users` - Member editors with roles and authentication
- `tasks` - Work items for the law review
- `assignments` - Many-to-many relationship between users and tasks
- `form_definitions` - Metadata for dynamically generated forms
- `form_submissions` - All form responses
- `attendance_log` - Event attendance records
- `system_config` - Key-value configuration store

See [REVISED_ARCHITECTURE.md](docs/REVISED_ARCHITECTURE.md) for detailed schema and ERD.

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate Google OAuth flow
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout current user

### Tasks
- `GET /tasks/` - Get user's tasks
- `POST /tasks/` - Create task (senior editor+)
- `PATCH /tasks/assignments/<id>/status` - Update task status

### Forms
- `GET /forms/` - List all forms
- `POST /forms/submissions` - Submit form response

### Attendance
- `GET /attendance/` - Get user's attendance
- `POST /attendance/log` - Log attendance

### API
- `GET /api/health` - Health check
- `GET /api/me` - Current user info
- `GET /api/stats` - User statistics

## Documentation

- [Revised Architecture](docs/REVISED_ARCHITECTURE.md) - New Flask + PostgreSQL architecture
- [Deployment Guide](docs/DEPLOYMENT.md) - Vercel deployment instructions
- [Implementation Plan](info/implementation.md) - Original technical implementation details
- [Substantive Content](info/substantive_content.md) - Functionality and workflows

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8, use type hints
- **SQL**: Use SQLAlchemy ORM, avoid raw queries
- **HTML/CSS**: Bootstrap 5, responsive design
- **JavaScript**: ES6+, async/await

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, commit
git add .
git commit -m "feat: description of changes"

# Push and create PR
git push origin feature/your-feature-name
```

### Testing

- Write tests for all new features
- Maintain >80% code coverage
- Test authentication flows thoroughly
- Mock external API calls

## Security

- ✅ Google OAuth 2.0 authentication
- ✅ Domain restriction to @stanford.edu
- ✅ PostgreSQL with prepared statements (SQL injection protection)
- ✅ CSRF protection with Flask-WTF
- ✅ Secure session management
- ✅ HTTPS only in production
- ✅ Environment variable-based secrets

## Performance

- PostgreSQL connection pooling
- Row-level locking for concurrent access
- Efficient batch operations
- Frontend caching with service workers
- CDN for static assets (Vercel)

## Monitoring

- Vercel function logs
- Database query performance monitoring
- Error tracking (can integrate Sentry)
- Health check endpoint at `/api/health`

## Cost Estimate

**Free Tier:**
- Vercel: Free (100GB bandwidth)
- Database: External PostgreSQL or Vercel Postgres free tier
- Total: $0/month (suitable for development)

**Production:**
- Vercel Pro: $20/month
- Managed PostgreSQL: $20-25/month
- OpenAI API: ~$50-100/month (usage-based)
- Total: ~$90-145/month

## License

See [LICENSE](LICENSE) file for details.

## Contributing

This is an internal Stanford Law Review project. For questions or contributions:
- Create an issue for bugs or feature requests
- Submit pull requests for review
- Contact the development team for access

## Support

For technical issues or questions, contact:
- Development team via GitHub issues
- Stanford Law Review IT department
