#!/bin/bash
# Setup script for LPanda Platform backend

set -e

echo "🐼 LPanda Platform Setup"
echo "========================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your configuration."
else
    echo "✅ .env file already exists"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Starting services with Docker Compose..."
docker-compose up -d postgres redis minio

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "📦 Installing Python dependencies..."
if command -v poetry &> /dev/null; then
    poetry install
else
    echo "⚠️  Poetry not found. Please install Poetry: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo "🗄️  Running database migrations..."
poetry run alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development server:"
echo "  poetry run uvicorn app.main:app --reload"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up"
echo ""
echo "Access the API at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
