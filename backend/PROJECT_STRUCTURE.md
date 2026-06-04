# LPanda Platform - Project Structure

## Overview

This document describes the complete project structure for the LPanda Platform backend.

## Directory Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files (auto-generated)
│   ├── env.py                  # Alembic environment configuration
│   └── script.py.mako          # Migration template
│
├── app/                        # Main application code
│   ├── api/                    # API routes and endpoints
│   │   └── __init__.py
│   │
│   ├── core/                   # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py           # Settings and environment variables
│   │   ├── database.py         # Database connection and session management
│   │   ├── redis.py            # Redis client configuration
│   │   ├── s3.py               # AWS S3 client configuration
│   │   └── logging.py          # Structured JSON logging
│   │
│   ├── models/                 # SQLAlchemy database models
│   │   └── __init__.py
│   │
│   ├── schemas/                # Pydantic schemas for validation
│   │   └── __init__.py
│   │
│   ├── services/               # Business logic layer
│   │   └── __init__.py
│   │
│   ├── tasks/                  # Celery background tasks
│   │   ├── __init__.py
│   │   └── deadline_enforcement.py  # Deadline penalty task
│   │
│   ├── __init__.py
│   ├── celery_app.py           # Celery configuration
│   └── main.py                 # FastAPI application entry point
│
├── scripts/                    # Utility scripts
│   └── setup.sh                # Automated setup script
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures and configuration
│   └── test_main.py            # Basic application tests
│
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Docker services configuration
├── Dockerfile                  # Container image definition
├── Makefile                    # Common development commands
├── PROJECT_STRUCTURE.md        # This file
├── pyproject.toml              # Poetry dependencies and config
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project documentation
├── requirements.txt            # Pip dependencies (alternative to Poetry)
└── SETUP.md                    # Setup instructions
```

## Key Components

### Core Configuration (`app/core/`)

**config.py**
- Loads environment variables using Pydantic Settings
- Provides type-safe configuration access
- Validates required settings on startup

**database.py**
- Configures async SQLAlchemy engine
- Implements connection pooling (5-20 connections)
- Provides database session dependency for FastAPI

**redis.py**
- Configures async Redis client
- Implements connection pooling (5-10 connections)
- Used for caching and session management

**s3.py**
- Configures boto3 S3 client
- Supports MinIO for local development
- Provides presigned URL generation for secure file access

**logging.py**
- Configures structured JSON logging
- Adds context (environment, service name) to all logs
- Supports both JSON and text formats

### Application Entry Point (`app/main.py`)

- Creates FastAPI application instance
- Configures CORS middleware
- Implements lifespan events for startup/shutdown
- Initializes Redis and S3 on startup
- Provides health check and root endpoints

### Background Jobs (`app/celery_app.py`, `app/tasks/`)

**celery_app.py**
- Configures Celery with Redis broker
- Defines periodic task schedule
- Sets task execution limits and timeouts

**deadline_enforcement.py**
- Implements deadline penalty checking (runs every 5 minutes)
- Placeholder for actual penalty logic (to be implemented in later tasks)

### Database Migrations (`alembic/`)

**env.py**
- Configures Alembic for async SQLAlchemy
- Imports models for autogenerate support
- Loads database URL from settings

**versions/**
- Contains timestamped migration files
- Auto-generated with `alembic revision --autogenerate`

### Testing (`tests/`)

**conftest.py**
- Provides pytest fixtures for async testing
- Creates test database and session
- Provides test client with dependency overrides

**test_main.py**
- Basic tests for root and health check endpoints
- Example of async test structure

## Configuration Files

### pyproject.toml
- Poetry dependency management
- Project metadata
- Build system configuration

### docker-compose.yml
Services:
- **postgres**: PostgreSQL 14 database
- **redis**: Redis 7 cache
- **minio**: S3-compatible storage
- **api**: FastAPI application
- **celery_worker**: Background job processor
- **celery_beat**: Task scheduler

### Dockerfile
- Multi-stage build (development and production)
- Installs Poetry and dependencies
- Creates non-root user for production
- Exposes port 8000

### .env.example
Contains all configurable environment variables:
- Application settings
- Database connection
- Redis connection
- AWS S3 credentials
- JWT configuration
- File upload limits
- Celery configuration
- Logging settings
- CORS origins

## Development Workflow

1. **Start infrastructure**: `docker-compose up -d postgres redis minio`
2. **Install dependencies**: `poetry install`
3. **Run migrations**: `poetry run alembic upgrade head`
4. **Start API**: `poetry run uvicorn app.main:app --reload`
5. **Start Celery worker**: `poetry run celery -A app.celery_app worker --loglevel=info`
6. **Start Celery beat**: `poetry run celery -A app.celery_app beat --loglevel=info`

Or use Docker Compose for everything: `docker-compose up`

## Next Steps

The following components will be implemented in subsequent tasks:

1. **Database Models** (`app/models/`)
   - User, Task, Submission, Points Transaction, etc.

2. **API Routes** (`app/api/`)
   - Authentication, Tasks, Submissions, Leaderboard, etc.

3. **Pydantic Schemas** (`app/schemas/`)
   - Request/response validation models

4. **Business Logic** (`app/services/`)
   - User management, task management, points calculation, etc.

5. **Background Tasks** (`app/tasks/`)
   - Complete deadline enforcement implementation
   - Leaderboard updates
   - Notifications

6. **Tests** (`tests/`)
   - Unit tests for services
   - Integration tests for API endpoints
   - Property-based tests for core logic

## Technology Stack Summary

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 14+ (via asyncpg)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic 1.13
- **Cache**: Redis 7+ (async)
- **Job Queue**: Celery 5.3
- **File Storage**: AWS S3 / MinIO
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Validation**: Pydantic 2.5
- **Testing**: pytest, pytest-asyncio, hypothesis
- **Logging**: python-json-logger

## Design Principles

1. **Async First**: All I/O operations use async/await
2. **Type Safety**: Pydantic for validation, type hints throughout
3. **Separation of Concerns**: Clear layers (API, services, models)
4. **Configuration Management**: Environment-based with validation
5. **Observability**: Structured logging for monitoring
6. **Testability**: Dependency injection, test fixtures
7. **Scalability**: Connection pooling, caching, background jobs
8. **Security**: JWT auth, password hashing, file validation

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
