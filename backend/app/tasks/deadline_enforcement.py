"""Apply the one-time Panda Points penalty for missed internal tasks."""
from datetime import datetime, timezone

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import DeadlinePenaltyApplied, Task, TaskAssignment, TaskSubmission
from app.services.points_service import PointsService


async def _check_deadline_penalties_async(db: AsyncSession | None = None) -> dict:
    """Penalize each overdue task assignment that has no submission.

    ``DeadlinePenaltyApplied`` provides the durable idempotency boundary. The
    optional session makes this job testable without opening a second database
    connection; production callers simply omit it.
    """
    owns_session = db is None
    if owns_session:
        db = AsyncSessionLocal()

    assert db is not None
    try:
        now = datetime.now(timezone.utc)
        submitted = exists().where(
            TaskSubmission.task_id == TaskAssignment.task_id,
            TaskSubmission.user_id == TaskAssignment.user_id,
        )
        already_penalized = exists().where(
            DeadlinePenaltyApplied.task_id == TaskAssignment.task_id,
            DeadlinePenaltyApplied.user_id == TaskAssignment.user_id,
        )
        overdue = (await db.execute(
            select(TaskAssignment.task_id, TaskAssignment.user_id)
            .join(Task, Task.id == TaskAssignment.task_id)
            .where(
                Task.deadline < now,
                Task.is_active.is_(True),
                Task.deleted_at.is_(None),
            )
        )).all()
        rows = (await db.execute(
            select(TaskAssignment.task_id, TaskAssignment.user_id)
            .join(Task, Task.id == TaskAssignment.task_id)
            .where(
                Task.deadline < now,
                Task.is_active.is_(True),
                Task.deleted_at.is_(None),
                ~submitted,
                ~already_penalized,
            )
            .with_for_update()
        )).all()

        for task_id, user_id in rows:
            db.add(DeadlinePenaltyApplied(task_id=task_id, user_id=user_id, penalty_amount=100))
            await PointsService.apply_deadline_penalty(db, user_id, task_id)

        await db.flush()
        if owns_session:
            await db.commit()
        return {
            "status": "completed",
            "tasks_checked": len(overdue),
            "penalties_applied": len(rows),
        }
    except Exception:
        if owns_session:
            await db.rollback()
        raise
    finally:
        if owns_session:
            await db.close()
