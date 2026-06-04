"""Celery application configuration for background jobs"""
from celery import Celery

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "lpanda_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.deadline_enforcement", "app.tasks.leaderboard_refresh"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "check-deadline-penalties": {
        "task": "app.tasks.deadline_enforcement.check_deadline_penalties",
        "schedule": 300.0,  # Run every 5 minutes
    },
    "refresh-leaderboard-cache": {
        "task": "app.tasks.leaderboard_refresh.refresh_leaderboard_cache",
        "schedule": 600.0,  # Run every 10 minutes
    },
}
