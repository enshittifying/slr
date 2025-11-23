# Deployment Guide: Vercel + PostgreSQL

This guide covers deploying the Stanford Law Review Workflow Management System to Vercel with a PostgreSQL database.

## Prerequisites

- GitHub account
- Vercel account (free tier is sufficient)
- PostgreSQL database (Vercel Postgres, Supabase, or Railway)
- Google Cloud Project with OAuth 2.0 credentials

## Step 1: Database Setup

### Option A: Vercel Postgres (Recommended)

1. Log in to [Vercel](https://vercel.com)
2. Go to Storage → Create Database → Postgres
3. Follow prompts to create database
4. Copy the `POSTGRES_URL` connection string

### Option B: External PostgreSQL (Supabase, Railway, etc.)

1. Create a PostgreSQL database on your preferred platform
2. Copy the connection string (format: `postgresql://user:password@host:port/database`)

## Step 2: Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Configure OAuth consent screen:
   - User Type: Internal (for stanford.edu)
   - Add authorized domain: `stanford.edu`
6. Create OAuth Client:
   - Application type: Web application
   - Authorized redirect URIs: `https://your-app.vercel.app/auth/callback`
7. Save Client ID and Client Secret

## Step 3: Google Service Account (for backend automation)

1. In Google Cloud Console, go to IAM & Admin → Service Accounts
2. Create Service Account
3. Grant permissions:
   - Google Sheets API (Editor)
   - Google Drive API (Editor)
   - Google Calendar API (Editor)
   - Google Forms API (Editor)
4. Create Key → JSON
5. Download the JSON file (keep it secure!)

## Step 4: Deploy to Vercel

### Via Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → Project
3. Import your GitHub repository
4. Configure project:
   - Framework Preset: Other
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
   - Install Command: `pip install -r requirements.txt`

### Via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd /path/to/slr
vercel --prod
```

## Step 5: Configure Environment Variables

In Vercel Dashboard → Project → Settings → Environment Variables, add:

### Required Variables

```bash
# Flask
SECRET_KEY=<generate-random-secret-key>
FLASK_ENV=production

# Database
POSTGRES_URL=<your-postgres-connection-string>

# Google OAuth
GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=https://your-app.vercel.app/auth/callback

# Google APIs
GOOGLE_SHEETS_ID=<your-master-sheet-id>
GOOGLE_CALENDAR_ID=<your-calendar-id>
GOOGLE_DRIVE_FOLDER_ID=<your-drive-folder-id>

# Service Account (paste entire JSON as string)
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Application
ALLOWED_DOMAIN=stanford.edu
```

### Optional Variables

```bash
# Database Access (if needed)
WESTLAW_API_KEY=...
LEXIS_API_KEY=...
JSTOR_API_KEY=...

# Configuration
MAX_CONCURRENT_TASKS=5
LOG_LEVEL=INFO
API_RATE_LIMIT_PER_MINUTE=60
LLM_RATE_LIMIT_PER_MINUTE=20

# Session
SESSION_COOKIE_SECURE=True
PERMANENT_SESSION_LIFETIME=3600
```

## Step 6: Initialize Database

After deployment, you need to create the database tables.

### Option A: Using Vercel CLI

```bash
# Install psql or use pgAdmin
psql $POSTGRES_URL

# Or run migration script
vercel env pull .env.production
python scripts/init_db.py
```

### Option B: Using Migration Script

Create `scripts/init_db.py`:

```python
import os
from web_app import create_app
from web_app.models import db

app = create_app('production')

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
```

Run locally with production env vars:

```bash
python scripts/init_db.py
```

## Step 7: Verify Deployment

1. Visit `https://your-app.vercel.app`
2. Click "Sign in with Google"
3. Verify authentication works
4. Check `/api/health` endpoint returns `{"status": "healthy"}`

## Step 8: Configure Custom Domain (Optional)

1. In Vercel Dashboard → Project → Settings → Domains
2. Add custom domain (e.g., `workflow.stanfordlawreview.org`)
3. Follow DNS configuration instructions
4. Update `GOOGLE_REDIRECT_URI` in environment variables to use new domain

## Troubleshooting

### Database Connection Issues

```bash
# Test connection locally
python -c "from sqlalchemy import create_engine; engine = create_engine('$POSTGRES_URL'); engine.connect()"
```

### OAuth Errors

- Verify redirect URI matches exactly in Google Console
- Check that OAuth consent screen is configured for stanford.edu
- Ensure Client ID and Secret are correct

### 500 Errors

- Check Vercel logs: Dashboard → Project → Functions → View Logs
- Verify all environment variables are set
- Check database tables are created

### Import Errors

- Ensure all dependencies are in `requirements.txt`
- Vercel Python runtime has some limitations - check compatibility

## Monitoring

### Vercel Logs

```bash
# View real-time logs
vercel logs --follow

# View logs for specific function
vercel logs api/index.py
```

### Database Monitoring

- For Vercel Postgres: Dashboard → Storage → [your-db] → Insights
- For external DB: Use provider's monitoring tools

## Scaling Considerations

### Free Tier Limits

- Vercel: 100GB bandwidth, serverless execution time limits
- Vercel Postgres: 256 MB storage, 60 hours compute time

### If You Exceed Limits

1. Upgrade Vercel plan (Pro: $20/month)
2. Use external PostgreSQL (unlimited)
3. Optimize database queries
4. Implement caching (Redis)
5. Use CDN for static assets

## Security Best Practices

1. **Rotate secrets regularly**: Generate new SECRET_KEY, rotate API keys
2. **Enable 2FA**: On Vercel and database provider accounts
3. **Monitor access logs**: Review who's accessing the application
4. **Keep dependencies updated**: Run `pip list --outdated` regularly
5. **Use environment-specific secrets**: Different keys for dev/prod

## Backup Strategy

### Database Backups

```bash
# Automated with Vercel Postgres (Pro tier)
# Manual backup:
pg_dump $POSTGRES_URL > backup_$(date +%Y%m%d).sql

# Restore:
psql $POSTGRES_URL < backup_20251112.sql
```

### Code Backups

- Git repository is the source of truth
- Vercel automatically keeps deployment history
- Consider additional backup to external service

## Rollback Procedure

If deployment fails:

```bash
# Via CLI
vercel rollback

# Via Dashboard
Dashboard → Project → Deployments → [select previous] → Promote to Production
```

## Cost Estimate

**Free Tier Setup:**
- Vercel: Free
- Vercel Postgres: Free (256 MB)
- Total: $0/month

**Production Setup:**
- Vercel Pro: $20/month
- Vercel Postgres Pro: $20/month
- External PostgreSQL (Supabase/Railway): $10-25/month
- OpenAI API: Pay as you go (~$50-100/month estimated)
- Total: ~$80-140/month

## Next Steps

1. Set up CI/CD with GitHub Actions
2. Configure monitoring and alerting
3. Set up automated database backups
4. Implement rate limiting and DDoS protection
5. Add error tracking (Sentry)
