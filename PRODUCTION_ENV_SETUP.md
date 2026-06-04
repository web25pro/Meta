# Production Environment Setup Guide

## Secure Keys Generated ✅

Your secure base64-encoded keys have been generated:

```
SECRET_KEY=4CwR5h48MAW+lwZsuI/v8mLkhO9wg4SPt+RQlmk14kw=
JWT_SECRET_KEY=F619ZrvwpfUb+eRmSpxrqV5eZ/8CnOsogWYhwj+4ziQ=
```

These are already in `.env.production`

---

## 1. Database Configuration (Supabase)

**Get your Supabase connection string:**

1. Go to [supabase.com](https://supabase.com) → Your Project
2. Click **Settings** → **Database**
3. Copy the **Connection string** (URI format)
4. Replace `[YOUR-PASSWORD]` with your database password

**Update in .env.production:**
```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres
```

Example:
```
DATABASE_URL=postgresql+asyncpg://postgres:mySecurePassword123@db.abc123xyz.supabase.co:5432/postgres
```

---

## 2. Redis Configuration (Upstash)

**Get your Upstash Redis URL:**

1. Go to [upstash.com](https://upstash.com) → Your Redis Database
2. Click **Details** tab
3. Copy the **Redis CLI** connection string or REST API URL
4. It should look like: `redis://default:password@endpoint.upstash.io:6379`

**Update in .env.production:**
```
REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379
CELERY_BROKER_URL=redis://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379/1
CELERY_RESULT_BACKEND=redis://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379/2
```

Example:
```
REDIS_URL=redis://default:abc123xyz@choice-goblin-12345.upstash.io:6379
CELERY_BROKER_URL=redis://default:abc123xyz@choice-goblin-12345.upstash.io:6379/1
CELERY_RESULT_BACKEND=redis://default:abc123xyz@choice-goblin-12345.upstash.io:6379/2
```

---

## 3. Email Configuration (SendGrid)

**Create SendGrid Account & Get API Key:**

1. Go to [sendgrid.com](https://sendgrid.com) → Create Account
2. Verify your sender email or domain
3. Go to **Settings** → **API Keys** → **Create API Key**
4. Copy the key (starts with `SG.`)

**Update in .env.production:**
```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.YOUR_FULL_API_KEY
EMAIL_FROM=noreply@yourdomain.com
```

Example:
```
SMTP_PASSWORD=SG.abc123xyz_complete_key_here
```

---

## 4. Domain Configuration

**Get your domain (if you don't have one):**
- Namecheap: $8-15/year
- GoDaddy: $12/year
- Route53: Domain registration available

**Update SITE_BASE_URL and CORS_ORIGINS:**
```
SITE_BASE_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

Example:
```
SITE_BASE_URL=https://lpanda.com
CORS_ORIGINS=https://lpanda.com,https://www.lpanda.com
ALLOWED_HOSTS=lpanda.com,www.lpanda.com
```

---

## 5. AWS S3 Configuration (Optional - for file uploads)

**For file upload functionality:**

1. Go to [AWS Console](https://aws.amazon.com)
2. Create S3 bucket: `lpanda-submissions-prod`
3. Create IAM user with S3 permissions
4. Get Access Key ID and Secret Access Key

**Update in .env.production:**
```
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## 6. Sentry Error Tracking (Optional but Recommended)

**Set up error tracking:**

1. Go to [sentry.io](https://sentry.io)
2. Create project → FastAPI
3. Get your DSN (looks like: `https://key@sentry.io/id`)

**Update in .env.production:**
```
SENTRY_DSN=https://YOUR_KEY@sentry.io/YOUR_PROJECT_ID
```

---

## 7. Run Database Migrations

Once all values are filled in:

```bash
cd backend

# Load production environment
$env:DATABASE_URL="your_production_database_url"

# Run migrations
alembic upgrade head
```

---

## 8. Deploy to Production

### Option 1: Railway (Recommended)

```bash
# Push to GitHub
git add .env.production
git commit -m "Add production environment"
git push origin main

# Railway auto-deploys on push
```

### Option 2: Manual Docker Deployment

```bash
# Build image
docker build -f backend/Dockerfile.prod -t lpanda-backend .

# Push to registry
docker tag lpanda-backend:latest your-account.dkr.ecr.us-east-1.amazonaws.com/lpanda-backend:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/lpanda-backend:latest

# Deploy to ECS/AppRunner with .env.production
```

---

## 9. Verify Production Setup

**Test database connection:**
```bash
python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    engine = create_async_engine('postgresql+asyncpg://...')
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT 1'))
        print('✅ Database connected')
    await engine.dispose()

asyncio.run(test())
"
```

**Test Redis connection:**
```bash
python -c "
import redis
r = redis.from_url('redis://...')
print('✅ Redis connected' if r.ping() else '❌ Redis failed')
"
```

**Test Email:**
```bash
# Manually verify SendGrid configuration in code
python -c "
import smtplib
from email.mime.text import MIMEText

server = smtplib.SMTP('smtp.sendgrid.net', 587)
server.starttls()
server.login('apikey', 'SG.YOUR_KEY')
print('✅ SendGrid SMTP connected')
server.quit()
"
```

---

## Complete Checklist Before Launch

- [ ] `SECRET_KEY` set to base64 string (not hardcoded text)
- [ ] `JWT_SECRET_KEY` set to base64 string (not hardcoded text)
- [ ] `DEBUG=false` in production
- [ ] `APP_ENV=production`
- [ ] Database URL points to Supabase
- [ ] Redis URL points to Upstash
- [ ] SendGrid API key configured
- [ ] Domain configured in `SITE_BASE_URL`
- [ ] CORS origins updated for your domain
- [ ] Migrations run successfully (`alembic upgrade head`)
- [ ] Sentry DSN configured (if using error tracking)
- [ ] Environment variables secured (never commit .env.production!)
- [ ] Database backups enabled
- [ ] SSL/HTTPS enforced

---

## Security Best Practices

✅ **DO:**
- Keep `.env.production` out of version control (add to `.gitignore`)
- Use Railway/Docker secrets management
- Rotate keys every 90 days
- Enable database backups
- Use HTTPS everywhere
- Monitor logs with Sentry
- Set up rate limiting

❌ **DON'T:**
- Commit secret keys to Git
- Use same secret key for development and production
- Share credentials in Slack/Discord
- Use weak passwords
- Disable SSL/HTTPS
- Expose debug information

---

## Environment Variable Template

Copy and customize:

```bash
# .env.production (NEVER COMMIT THIS FILE)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres
REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_HOST:6379
SMTP_PASSWORD=SG.YOUR_SENDGRID_API_KEY
SECRET_KEY=4CwR5h48MAW+lwZsuI/v8mLkhO9wg4SPt+RQlmk14kw=
JWT_SECRET_KEY=F619ZrvwpfUb+eRmSpxrqV5eZ/8CnOsogWYhwj+4ziQ=
SITE_BASE_URL=https://yourdomain.com
```

---

Need help? Use this guide to fill in each value, then deploy! 🚀
