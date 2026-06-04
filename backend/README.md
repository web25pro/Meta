# LPanda Platform Backend

FastAPI-based backend for the LPanda Meta-Jungle Task & Reward Management Platform.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Relational database with async support
- **Redis**: Caching and session management
- **AWS S3**: File storage (MinIO for local development)
- **Celery**: Background job processing for deadline enforcement
- **Alembic**: Database migrations
- **Structured Logging**: JSON logging for monitoring

## Prerequisites

- Python 3.10+
- Docker and Docker Compose (for local development)
- Poetry (for dependency management)

## Quick Start

### Using Docker Compose (Recommended)

1. Copy environment variables:
```bash
cp .env.example .env
```

2. Start all services:
```bash
docker-compose up -d
```

3. Run database migrations:
```bash
docker-compose exec api alembic upgrade head
```

4. Access the API:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

### Local Development

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start PostgreSQL and Redis:
```bash
docker-compose up -d postgres redis minio
```

4. Run migrations:
```bash
poetry run alembic upgrade head
```

5. Start the development server:
```bash
poetry run uvicorn app.main:app --reload
```

6. Start Celery worker (in another terminal):
```bash
poetry run celery -A app.celery_app worker --loglevel=info
```

7. Start Celery beat (in another terminal):
```bash
poetry run celery -A app.celery_app beat --loglevel=info
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic configuration
├── app/
│   ├── core/            # Core configuration
│   │   ├── config.py    # Settings management
│   │   ├── database.py  # Database connection
│   │   ├── redis.py     # Redis client
│   │   ├── s3.py        # S3 client
│   │   └── logging.py   # Logging configuration
│   ├── tasks/           # Celery tasks
│   │   └── deadline_enforcement.py
│   ├── celery_app.py    # Celery configuration
│   └── main.py          # FastAPI application
├── tests/               # Test files
├── .env.example         # Example environment variables
├── docker-compose.yml   # Docker services
├── Dockerfile           # Container image
└── pyproject.toml       # Python dependencies
```

## Database Migrations

Create a new migration:
```bash
poetry run alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
poetry run alembic upgrade head
```

Rollback migration:
```bash
poetry run alembic downgrade -1
```

## Testing

Run tests:
```bash
poetry run pytest
```

Run tests with coverage:
```bash
poetry run pytest --cov=app --cov-report=html
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `S3_BUCKET_NAME`: S3 bucket for file storage
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `SECRET_KEY`: Application secret key

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Background Jobs

The platform uses Celery for background job processing:

- **Deadline Enforcement**: Runs every 5 minutes to check for missed deadlines and apply penalties
- **Leaderboard Updates**: Updates cached leaderboard rankings
- **Notifications**: Sends email and in-app notifications

## Monitoring

Logs are output in JSON format for easy parsing and monitoring. Configure log level with `LOG_LEVEL` environment variable.

## Production Deployment

1. Build production image:
```bash
docker build --target production -t lpanda-api:latest .
```

2. Set production environment variables
3. Run database migrations
4. Deploy with orchestration tool (Kubernetes, ECS, etc.)

## License

Proprietary - LPanda Team
