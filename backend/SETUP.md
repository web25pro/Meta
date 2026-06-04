# LPanda Platform - Setup Guide

This guide will help you set up the LPanda Platform backend for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher**: [Download Python](https://www.python.org/downloads/)
- **Docker Desktop**: [Download Docker](https://www.docker.com/products/docker-desktop/)
- **Poetry** (recommended) or pip: [Install Poetry](https://python-poetry.org/docs/#installation)

## Quick Setup (Automated)

Run the setup script:

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:
1. Create `.env` file from `.env.example`
2. Start PostgreSQL, Redis, and MinIO with Docker
3. Install Python dependencies
4. Run database migrations

## Manual Setup

### 1. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and update the following critical values:

```env
SECRET_KEY=your-secret-key-here-change-this
JWT_SECRET_KEY=your-jwt-secret-key-here-change-this
```

For local development, the default values for database, Redis, and MinIO should work.

### 2. Start Infrastructure Services

Start PostgreSQL, Redis, and MinIO:

```bash
docker-compose up -d postgres redis minio
```

Verify services are running:

```bash
docker-compose ps
```

### 3. Install Python Dependencies

**Using Poetry (recommended):**

```bash
poetry install
```

**Using pip:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Database Setup

Run migrations to create database tables:

```bash
# With Poetry
poetry run alembic upgrade head

# With pip
alembic upgrade head
```

### 5. Start the Application

**Option A: Run locally with hot reload**

```bash
# With Poetry
poetry run uvicorn app.main:app --reload

# With pip
uvicorn app.main:app --reload
```

**Option B: Run everything with Docker Compose**

```bash
docker-compose up
```

This starts:
- FastAPI application (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Celery worker
- Celery beat scheduler

### 6. Verify Installation

Open your browser and visit:

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MinIO Console**: http://localhost:9001 (login: minioadmin/minioadmin)

## Running Background Jobs

The platform uses Celery for background tasks like deadline enforcement.

**Start Celery worker:**

```bash
# With Poetry
poetry run celery -A app.celery_app worker --loglevel=info

# With pip
celery -A app.celery_app worker --loglevel=info
```

**Start Celery beat (scheduler):**

```bash
# With Poetry
poetry run celery -A app.celery_app beat --loglevel=info

# With pip
celery -A app.celery_app beat --loglevel=info
```

## Database Migrations

**Create a new migration:**

```bash
poetry run alembic revision --autogenerate -m "description of changes"
```

**Apply migrations:**

```bash
poetry run alembic upgrade head
```

**Rollback last migration:**

```bash
poetry run alembic downgrade -1
```

## Running Tests

**Run all tests:**

```bash
poetry run pytest
```

**Run with coverage:**

```bash
poetry run pytest --cov=app --cov-report=html
```

View coverage report: `open htmlcov/index.html`

## MinIO Setup (S3-Compatible Storage)

For local development, we use MinIO as an S3-compatible storage service.

1. Access MinIO Console: http://localhost:9001
2. Login with: `minioadmin` / `minioadmin`
3. Create a bucket named `lpanda-submissions`
4. Set bucket policy to allow uploads

Update your `.env`:

```env
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=lpanda-submissions
S3_ENDPOINT_URL=http://localhost:9000
```

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8000  # On macOS/Linux
netstat -ano | findstr :8000  # On Windows

# Stop the process or change the port in .env
PORT=8001
```

### Database Connection Error

Ensure PostgreSQL is running:

```bash
docker-compose ps postgres
docker-compose logs postgres
```

### Redis Connection Error

Ensure Redis is running:

```bash
docker-compose ps redis
docker-compose logs redis
```

### Import Errors

Ensure you're in the correct directory and virtual environment:

```bash
# Check current directory
pwd  # Should be in backend/

# Activate virtual environment
poetry shell  # With Poetry
source venv/bin/activate  # With pip
```

## Development Workflow

1. **Make code changes** in `app/` directory
2. **Create/update tests** in `tests/` directory
3. **Run tests** to ensure everything works
4. **Create database migration** if models changed
5. **Update documentation** if needed

## Useful Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart api

# Access database
docker-compose exec postgres psql -U lpanda -d lpanda_db

# Access Redis CLI
docker-compose exec redis redis-cli

# Run shell in API container
docker-compose exec api bash
```

## Next Steps

After setup is complete:

1. Review the [README.md](README.md) for project structure
2. Check [design.md](.kiro/specs/lpanda-task-reward-platform/design.md) for architecture details
3. Start implementing features according to [tasks.md](.kiro/specs/lpanda-task-reward-platform/tasks.md)

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify all services are healthy: `docker-compose ps`
3. Review environment variables in `.env`
4. Consult the [design document](.kiro/specs/lpanda-task-reward-platform/design.md)
