# Deployment Guide - Stanford Law Review Citation System

Complete guide to deploying the system to production.

---

## Prerequisites

- Google Cloud account with billing enabled
- Vercel account
- OpenAI API key
- Google OAuth credentials

---

## Step 1: Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen:
   - User Type: Internal (for Stanford only)
   - App name: Stanford Law Review Citation System
   - User support email: your-email@stanford.edu
   - Developer email: your-email@stanford.edu
6. Create OAuth Client ID:
   - Application type: Web application
   - Name: SLR Citation System
   - Authorized redirect URIs:
     - Development: `http://localhost:3000/api/auth/callback/google`
     - Production: `https://slro.vercel.app/api/auth/callback/google`
7. Save Client ID and Client Secret

---

## Step 2: Deploy Backend to Cloud Run

### 2.1: Set Up Cloud SQL

```bash
# Set your GCP project
gcloud config set project YOUR_PROJECT_ID

# Create Cloud SQL instance
gcloud sql instances create slr-db \
  --database-version=POSTGRES_15 \
  --tier=db-g1-small \
  --region=us-west1 \
  --root-password=SECURE_PASSWORD_HERE

# Create database
gcloud sql databases create slr_production --instance=slr-db

# Get connection name
gcloud sql instances describe slr-db --format="value(connectionName)"
# Output: project-id:us-west1:slr-db
```

### 2.2: Store Secrets in Secret Manager

```bash
# Create secrets
echo -n "postgresql+asyncpg://postgres:PASSWORD@/slr_production?host=/cloudsql/CONNECTION_NAME" | \
  gcloud secrets create database-url --data-file=-

echo -n "sk-YOUR_OPENAI_KEY" | \
  gcloud secrets create openai-key --data-file=-

echo -n "$(openssl rand -hex 32)" | \
  gcloud secrets create secret-key --data-file=-

# Verify
gcloud secrets list
```

### 2.3: Build and Deploy Backend

```bash
cd backend

# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/slr-api:latest

# Deploy to Cloud Run
gcloud run deploy slr-api \
  --image gcr.io/YOUR_PROJECT_ID/slr-api:latest \
  --platform managed \
  --region us-west1 \
  --allow-unauthenticated \
  --add-cloudsql-instances YOUR_PROJECT:us-west1:slr-db \
  --set-secrets="DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-key:latest,SECRET_KEY=secret-key:latest" \
  --set-env-vars="ENVIRONMENT=production,GOOGLE_CLIENT_ID=YOUR_CLIENT_ID,ALLOWED_ORIGINS=https://slro.vercel.app" \
  --min-instances=0 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300

# Get the URL
gcloud run services describe slr-api --region us-west1 --format="value(status.url)"
# Output: https://slr-api-xxxxx-uw.a.run.app
```

### 2.4: Run Database Migrations

```bash
# Connect to Cloud SQL via proxy
./cloud-sql-proxy YOUR_PROJECT:us-west1:slr-db &

# In another terminal
cd backend
export DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@localhost:5432/slr_production"
alembic upgrade head

# Seed initial data (optional)
python scripts/seed_database.py
```

---

## Step 3: Deploy Frontend to Vercel

### 3.1: Install Vercel CLI

```bash
npm i -g vercel
```

### 3.2: Deploy Frontend

```bash
cd frontend

# Login to Vercel
vercel login

# Deploy (first time)
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: slr-frontend
# - Directory: ./
# - Override settings? No

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL production
# Paste: https://slr-api-xxxxx-uw.a.run.app

vercel env add NEXTAUTH_URL production
# Paste: https://slro.vercel.app

vercel env add NEXTAUTH_SECRET production
# Paste: $(openssl rand -base64 32)

vercel env add GOOGLE_CLIENT_ID production
# Paste: your_client_id.apps.googleusercontent.com

vercel env add GOOGLE_CLIENT_SECRET production
# Paste: your_client_secret

# Deploy to production
vercel --prod

# Set custom domain (optional)
vercel domains add slro.vercel.app
```

### 3.3: Alternative - Deploy via Vercel Dashboard

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure:
   - Framework Preset: Next.js
   - Root Directory: `frontend`
   - Build Command: `npm run build`
4. Add environment variables in dashboard:
   ```
   NEXT_PUBLIC_API_URL=https://slr-api-xxxxx-uw.a.run.app
   NEXTAUTH_URL=https://slro.vercel.app
   NEXTAUTH_SECRET=generate_with_openssl
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```
5. Deploy

---

## Step 4: Set Up Google Cloud Storage

```bash
# Create bucket for PDFs
gcloud storage buckets create gs://slr-pdfs \
  --location=us-west1 \
  --uniform-bucket-level-access

# Set lifecycle policy (archive old files)
cat > lifecycle.json <<EOF
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
EOF

gcloud storage buckets update gs://slr-pdfs --lifecycle-file=lifecycle.json
```

---

## Step 5: Set Up Pub/Sub (for Pipeline)

```bash
# Create topics
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

## Step 6: Deploy Cloud Functions (Pipeline)

*Note: Cloud Functions are not yet implemented. This is the planned setup.*

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
```

---

## Step 7: Set Up Monitoring

### 7.1: Cloud Monitoring Alerts

```bash
# Create alert for API errors
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="SLR API High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND severity="ERROR"'
```

### 7.2: Sentry (Optional)

1. Sign up at https://sentry.io
2. Create new project
3. Get DSN
4. Add to backend environment:
   ```bash
   gcloud run services update slr-api \
     --set-env-vars="SENTRY_DSN=your_sentry_dsn"
   ```

---

## Step 8: Update DNS (Optional)

If using custom domain slro.vercel.app:

1. Go to Vercel dashboard → Settings → Domains
2. Add domain: slro.vercel.app
3. Follow Vercel's DNS instructions
4. Update Google OAuth redirect URIs

---

## Step 9: Create Initial Admin User

```bash
# Connect to database
psql "postgresql://postgres:PASSWORD@/slr_production?host=/cloudsql/CONNECTION_NAME"

# Create admin user
INSERT INTO users (id, email, full_name, role, is_active, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'admin@stanford.edu',
  'Admin User',
  'admin',
  TRUE,
  NOW(),
  NOW()
);
```

---

## Step 10: Test the Deployment

### Backend Health Check

```bash
curl https://slr-api-xxxxx-uw.a.run.app/health
```

Expected:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0"
}
```

### Frontend

Visit https://slro.vercel.app

- Should show landing page
- Click "Sign In" → Google OAuth flow
- Should redirect to dashboard after login

### API with Authentication

```bash
# Get Google ID token (from browser after login)
TOKEN="your_google_id_token"

curl -H "Authorization: Bearer $TOKEN" \
     https://slr-api-xxxxx-uw.a.run.app/api/v1/users/me
```

---

## Cost Estimates

### Monthly Costs (Production)

- **Cloud SQL (db-g1-small)**: ~$25/month
- **Cloud Run API**: ~$5/month (50k requests)
- **Cloud Storage**: ~$10/month (500 GB)
- **Pub/Sub**: ~$1/month
- **Cloud Logging**: ~$10/month (200 GB)
- **Vercel**: $0 (free tier for education)
- **OpenAI API**: ~$50/month (GPT-4o-mini)

**Total: ~$100/month**

---

## Maintenance

### Update Backend

```bash
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/slr-api:latest
gcloud run deploy slr-api \
  --image gcr.io/YOUR_PROJECT_ID/slr-api:latest \
  --region us-west1
```

### Update Frontend

```bash
cd frontend
vercel --prod
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply to production
./cloud-sql-proxy YOUR_PROJECT:us-west1:slr-db &
alembic upgrade head
```

### View Logs

```bash
# Backend logs
gcloud run logs tail slr-api --region us-west1

# Cloud Function logs
gcloud functions logs read sp-machine --region us-west1
```

---

## Rollback

### Backend

```bash
# List revisions
gcloud run revisions list --service=slr-api --region=us-west1

# Rollback to previous revision
gcloud run services update-traffic slr-api \
  --region=us-west1 \
  --to-revisions=REVISION_NAME=100
```

### Frontend

In Vercel dashboard → Deployments → Click previous deployment → "Promote to Production"

---

## Security Checklist

- [ ] Google OAuth configured with stanford.edu restriction
- [ ] Database passwords are strong and stored in Secret Manager
- [ ] NEXTAUTH_SECRET is random and secure
- [ ] Cloud SQL has private IP only (no public access)
- [ ] Cloud Run service uses least-privilege service account
- [ ] CORS configured to only allow Vercel domain
- [ ] Rate limiting enabled (if using Cloud Armor)
- [ ] Automated backups enabled for Cloud SQL
- [ ] Monitoring and alerts configured

---

## Troubleshooting

### Backend won't start

1. Check Cloud Run logs: `gcloud run logs tail slr-api`
2. Verify secrets are accessible
3. Test database connection via Cloud SQL Proxy

### Frontend can't connect to backend

1. Verify NEXT_PUBLIC_API_URL is correct
2. Check CORS settings in backend
3. Verify Cloud Run allows unauthenticated requests

### Authentication fails

1. Verify Google OAuth redirect URIs match exactly
2. Check NEXTAUTH_URL matches deployment URL
3. Verify @stanford.edu domain restriction

---

## Support

- **Documentation**: See `/info` directory
- **Backend API Docs**: https://slr-api-xxxxx-uw.a.run.app/docs
- **Frontend**: https://slro.vercel.app

---

**Deployment complete! 🚀**
