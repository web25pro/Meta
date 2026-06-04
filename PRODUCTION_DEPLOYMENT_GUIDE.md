# LPanda Platform - Production Deployment Guide

## 🎯 Executive Summary
To launch LPanda as a fully functional production site accessible to everyone, you need to:
1. **Set up backend infrastructure** (Postgres, Redis, Email)
2. **Complete & test backend API**
3. **Build & optimize frontend**
4. **Deploy both to production hosting**
5. **Set up monitoring & security**

**Estimated Timeline:** 2-3 weeks (working full-time)

---

## Phase 1: Backend Infrastructure Setup (Days 1-3)

### 1.1 Database (Supabase PostgreSQL)
**What's needed:** Postgres database to store users, tasks, verification tokens, password reset tokens

**Setup with Supabase (Recommended):**
1. Go to [supabase.com](https://supabase.com)
2. Click "Create a new project"
3. Fill in project name (e.g., "lpanda-production")
4. Choose region closest to you
5. Set a strong database password
6. Wait for setup (2-3 minutes)
7. Copy connection string from Settings → Database → Connection String

**Get Connection String:**
- Go to Supabase Dashboard → Settings → Database
- Copy the "Connection string" (URI format)
- Replace `[YOUR-PASSWORD]` with your database password
- Should look like: `postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres`

**Cost:** $5-25/month (free tier: 500MB)

**Post-Setup Action:**
```bash
# Run Alembic migrations to create tables
cd backend
export DATABASE_URL="postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres"
alembic upgrade head
```

### 1.2 Redis (Session & Background Jobs - Backend)
**What's needed:** Redis for token caching, session management, background job queue (Celery)

**Setup Options:**

**Option A: Upstash Redis (Recommended - Easiest)**
1. Go to [upstash.com](https://upstash.com)
2. Sign up with GitHub
3. Create a new Redis database
4. Choose region (same as backend for best performance)
5. Copy connection string: `redis://default:password@endpoint:port`

**Option B: AWS ElastiCache**
- Cost: ~$15/month
- Setup: AWS Console → ElastiCache → Create cluster

**Option C: Railway Redis**
- Cost: Built-in $5/month
- Setup: Railway dashboard → Add service → Redis

**Get Connection String (Upstash):**
- Dashboard → Database → Copy "Redis CLI" or REST API url
- Format: `redis://default:password@endpoint.upstash.io:port`

**Cost:** 
- Upstash: Pay-per-request (~$1-5/month for small app)
- AWS ElastiCache: ~$15/month
- Railway: $5/month included

**Post-Setup Action:**
```bash
# Update backend/.env
REDIS_URL=redis://default:your_password@endpoint.upstash.io:port

# Test connection
python -c "import redis; r = redis.from_url('redis://...'); print(r.ping())"
```

### 1.3 Email Service (SMTP)
**What's needed:** Send verification emails, password reset emails, notifications

**Options:**
- **SendGrid** (Recommended)
  - Cost: Free tier = 100 emails/day
  - Setup: Create account → Generate API key
  
- **AWS SES** (Cheapest at scale)
  - Cost: $0.10 per 1000 emails
  - Setup: AWS Console → SES → Verify domain
  
- **Gmail SMTP** (Quick setup for testing)
  - Cost: Free (but limited to 500 emails/day)
  - Setup: Enable "Less secure app access"

**Update backend/.env:**
```
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your_api_key_here
SMTP_FROM_EMAIL=noreply@yoursite.com
```

---

## Phase 2: Backend API Completion & Testing (Days 2-5)

### 2.1 Verify All Endpoints Work
Test each endpoint manually:

```bash
# 1. Register new user
curl -X POST http://localhost:8000/api/v1/community/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/community/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'

# 3. Verify email (using token from email)
curl -X POST http://localhost:8000/api/v1/community/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "verification_token_from_email"}'

# 4. Request password reset
curl -X POST http://localhost:8000/api/v1/community/password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 5. Confirm password reset
curl -X POST http://localhost:8000/api/v1/community/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset_token_from_email",
    "new_password": "NewPass456"
  }'
```

### 2.2 Add Production Configuration
**backend/.env.production:**
```
# Supabase Database
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db.your-project.supabase.co:5432/postgres

# Redis (Upstash)
REDIS_URL=redis://default:your_password@endpoint.upstash.io:port

# Email
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_key

# JWT
SECRET_KEY=your_long_secret_key_generate_with_openssl
ALGORITHM=HS256

# CORS
ALLOWED_ORIGINS=https://yourdomain.com

# Environment
DEBUG=false
ENVIRONMENT=production

# Supabase Settings (optional - for additional Supabase features)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_public_key
```

**How to Get Supabase Connection Strings:**
1. Go to Supabase Dashboard
2. Click Settings → Database
3. Find "Connection string" 
4. Copy URI format (looks like `postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres`)

**How to Get Redis URL:**
1. Go to Upstash Dashboard
2. Click your database
3. Click "Details" tab
4. Copy the "Redis CLI" command or REST URL
5. Format: `redis://default:password@host:port`

**Update in backend/app/main.py:**
```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
```

### 2.3 Add Error Tracking (Sentry)
```bash
# Already mentioned in backend - verify setup
pip install sentry-sdk
```

Update `backend/app/main.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if not settings.DEBUG:
    sentry_sdk.init(
        dsn="https://your_sentry_dsn@sentry.io/project_id",
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
    )
```

### 2.4 Add Rate Limiting
```bash
pip install slowapi
```

Update `backend/app/main.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### 2.5 Create Dockerfile for Backend
**backend/Dockerfile.prod:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Run migrations and start
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

---

## Phase 3: Frontend Build & Deployment (Days 3-4)

### 3.1 Production Build
```bash
cd frontend

# Build optimized production bundle
npm run build

# Test production build locally
npm run start
```

### 3.2 Environment Configuration
**frontend/.env.production:**
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
NEXT_PUBLIC_ENVIRONMENT=production
```

### 3.3 Security Headers
Update **frontend/next.config.js:**
```javascript
module.exports = {
  headers: async () => {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-DNS-Prefetch-Control', value: 'on' },
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ];
  },
};
```

### 3.4 Create Dockerfile for Frontend
**frontend/Dockerfile.prod:**
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./

EXPOSE 3000
CMD ["npm", "start"]
```

---

## Phase 4: Production Hosting & Deployment (Days 4-5)

### Option A: Railway.app (Recommended - Easiest)
1. Push code to GitHub
2. Go to railway.app → Create project
3. Connect GitHub repo
4. Add Postgres plugin
5. Add Redis plugin
6. Set environment variables
7. Deploy (automatic on git push)

**Cost:** $5-15/month starting

### Option B: AWS (Most Control - Harder)
1. **Push Docker images to ECR**
   ```bash
   aws ecr get-login-token --region us-east-1 | docker login --username AWS --password-stdin your-account-id.dkr.ecr.us-east-1.amazonaws.com
   
   docker build -f backend/Dockerfile.prod -t lpanda-backend .
   docker tag lpanda-backend:latest your-account-id.dkr.ecr.us-east-1.amazonaws.com/lpanda-backend:latest
   docker push your-account-id.dkr.ecr.us-east-1.amazonaws.com/lpanda-backend:latest
   ```

2. **Deploy with ECS or App Runner**
3. **Set up RDS, ElastiCache**
4. **Configure load balancer & SSL**

**Cost:** $20-100+/month

### Option C: Vercel (Frontend) + Railway (Backend)
- Frontend: Deploy to Vercel (free tier available)
- Backend: Deploy to Railway ($5-15/month)
- Connect via API_URL env var

**Process:**
```bash
# Frontend to Vercel
cd frontend
npm install -g vercel
vercel --prod

# Backend to Railway (via GitHub integration)
```

### 4.1 Set Up SSL/HTTPS
- **Railway/Vercel:** Automatic with Let's Encrypt
- **AWS:** Use ACM (AWS Certificate Manager) - free
- **Custom domain:** Point DNS records to your host

### 4.2 Configure Domain & DNS
1. Buy domain (Namecheap, GoDaddy, etc.)
2. Point DNS to your host:
   - Frontend A record → your-frontend-host
   - Backend A record (api.yourdomain.com) → your-backend-host

---

## Phase 5: Testing & Launch (Days 5-7)

### 5.1 End-to-End Testing Checklist
```
[ ] User registration works
[ ] Verification email sent and received
[ ] Email verification link works
[ ] Login with verified email
[ ] Password reset email sent
[ ] Password reset link works
[ ] New password accepted
[ ] JWT token refresh works
[ ] Logout clears tokens
[ ] Dashboard loads for authenticated users
[ ] Profile page displays user info
[ ] Referral code generated
[ ] Community pages accessible
[ ] Mobile responsive design works
[ ] Performance acceptable (<3s load time)
```

### 5.2 Load Testing
```bash
npm install -g artillery

# Create load-test.yml
# Run: artillery quick --count 100 --num 10 https://yourdomain.com
```

### 5.3 Security Audit
- [ ] No credentials in code
- [ ] HTTPS enforced
- [ ] CORS properly configured
- [ ] Rate limiting active
- [ ] SQL injection prevention (SQLAlchemy handles this)
- [ ] XSS protection (Next.js built-in)
- [ ] CSRF tokens on forms

### 5.4 Monitoring Setup
```bash
# Install monitoring
# Sentry: Already configured
# Monitoring dashboard: Railway/AWS CloudWatch
# Logging: Check application logs
```

---

## Immediate Action Items (This Week)

### Day 1: Infrastructure
1. ✅ Choose hosting platform (recommend Railway.app for ease)
2. ✅ Set up Postgres database
3. ✅ Set up Redis
4. ✅ Set up SendGrid for email
5. ✅ Create production .env files

### Day 2-3: Backend
1. ✅ Run Alembic migrations
2. ✅ Test all API endpoints
3. ✅ Add Sentry integration
4. ✅ Create backend Dockerfile
5. ✅ Push to GitHub

### Day 3-4: Frontend
1. ✅ Run production build
2. ✅ Create frontend Dockerfile
3. ✅ Set up environment variables
4. ✅ Add security headers
5. ✅ Deploy to Vercel or Railway

### Day 5: Connect & Test
1. ✅ Point frontend API_URL to production backend
2. ✅ Run full end-to-end tests
3. ✅ Verify email flow works
4. ✅ Test registration → verification → login
5. ✅ Load testing

---

## Post-Launch Checklist

- [ ] Daily log monitoring
- [ ] Weekly database backups verified
- [ ] Monthly security updates
- [ ] Analytics dashboard setup
- [ ] User feedback collection
- [ ] Performance optimization
- [ ] Auto-scaling configured

---

## Estimated Costs (Per Month)

| Service | Free Tier | Paid Tier | Recommended |
|---------|-----------|-----------|------------|
| Frontend Hosting | Vercel | - | $0-20 |
| Backend Hosting | - | $5-20 | Railway $10 |
| Database (Supabase Postgres) | 500MB | $5-25 | Supabase $10 |
| Redis (Upstash) | 10K commands | Pay-per-use | ~$1-5 |
| Email (SendGrid) | 100/day | $20+ | Free tier |
| Monitoring (Sentry) | 5k events/mo | $29+ | Free tier |
| Domain | - | $12/year | $12 |
| **TOTAL** | ~$0 | ~$80-130 | ~$25-40 |

**Free tier option:** You can stay on $0/month using free tiers (limited scale)
- Supabase: 500MB storage, 5MB/sec bandwidth
- Upstash: 10K commands/day free

**Breakdown for your setup:**
- Frontend (Vercel free): $0
- Backend (Railway): $10
- Supabase Postgres: $10 (after free tier)
- Upstash Redis: $1-5 (pay-per-use, very cheap)
- SendGrid email: Free (100/day)
- Sentry monitoring: Free (5k events)
- **Total: ~$21-25/month**

---

## Next Steps

1. **Choose your hosting** (Railway recommended)
2. **Send me which option you prefer** - I can help you set it up
3. **Create production databases** - link connection strings
4. **Deploy backend & frontend** - I can provide deployment scripts
5. **Run end-to-end tests** - verify everything works
6. **Launch!**

---

Need help with any specific step? Let me know which one to start with!
