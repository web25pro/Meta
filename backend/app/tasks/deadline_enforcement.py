"""Deadline enforcement background task"""
import asyncio
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError

from app.celery_app import celery_app
from app.core.logging import get_logger
from app.core.database import async_session_maker
from app.models import Task, TaskAssignment, TaskSubmission, DeadlinePenaltyApplied, User
from app.services.points_service import PointsService

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.deadline_enforcement.check_deadline_penalties")
def check_deadline_penalties():
    """
    Check for missed task deadlines and apply penalties.
    
    This task runs every 5 minutes to identify tasks with passed deadlines
    where users have not submitted, and applies the 100 PP penalty.
    
    The function ensures idempotency by checking the deadline_penalties_applied
    table before applying penalties.
    
    Returns:
        dict: Statistics about the penalty check operation
    """
    logger.info("Starting deadline penalty check")
    
    try:
        # Run the async function
        result = asyncio.run(_check_deadline_penalties_async())
        
        logger.info(
            f"Deadline penalty check completed: {result['penalties_applied']} penalties applied, "
            f"{result['tasks_checked']} tasks checked"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in deadline penalty check: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "penalties_applied": 0,
            "tasks_checked": 0
        }


async def _check_deadline_penalties_async():
    """
    Async implementation of deadline penalty check.
    
    Returns:
        dict: Statistics about the operation
    """
    async with async_session_maker() as db:
        try:
            # Get all tasks with deadlines in the past that are not deleted
            now = datetime.utcnow()
            result = await db.execute(
                select(Task).where(
                    and_(
                        Task.deadline < now,
                        Task.deleted_at.is_(None)
                    )
                )
            )
            overdue_tasks = result.scalars().all()
            
            if not overdue_tasks:
                logger.info("No overdue tasks found")
                return {
                    "status": "completed",
                    "penalties_applied": 0,
                    "tasks_checked": 0
                }
            
            logger.info(f"Found {len(overdue_tasks)} overdue tasks")
            
            penalties_applied = 0
            tasks_checked = 0
            
            for task in overdue_tasks:
                tasks_checked += 1
                
                # Get all users assigned to this task
                result = await db.execute(
                    select(TaskAssignment).where(TaskAssignment.task_id == task.id)
                )
                assignments = result.scalars().all()
                
                for assignment in assignments:
                    # Check if user has submitted this task
                    result = await db.execute(
                        select(TaskSubmission).where(
                            and_(
                                TaskSubmission.task_id == task.id,
                                TaskSubmission.user_id == assignment.user_id
                            )
                        )
                    )
                    submission = result.scalar_one_or_none()
                    
                    # If no submission, check if penalty already applied
                    if not submission:
                        result = await db.execute(
                            select(DeadlinePenaltyApplied).where(
                                and_(
                                    DeadlinePenaltyApplied.task_id == task.id,
                                    DeadlinePenaltyApplied.user_id == assignment.user_id
                                )
                            )
                        )
                        penalty_record = result.scalar_one_or_none()
                        
                        # If penalty not already applied, apply it
                        if not penalty_record:
                            try:
                                # Apply penalty
                                await PointsService.apply_deadline_penalty(
                                    db=db,
                                    user_id=assignment.user_id,
                                    task_id=task.id
                                )
                                
                                # Record that penalty was applied
                                penalty_applied = DeadlinePenaltyApplied(
                                    task_id=task.id,
                                    user_id=assignment.user_id
                                )
                                db.add(penalty_applied)
                                await db.commit()
                                
                                penalties_applied += 1
                                logger.info(
                                    f"Applied deadline penalty for user {assignment.user_id} "
                                    f"on task {task.id}"
                                )
                                
                            except IntegrityError:
                                # Penalty already applied (race condition)
                                await db.rollback()
                                logger.warning(
                                    f"Penalty already applied for user {assignment.user_id} "
                                    f"on task {task.id} (race condition)"
                                )
                            except Exception as e:
                                await db.rollback()
                                logger.error(
                                    f"Error applying penalty for user {assignment.user_id} "
                                    f"on task {task.id}: {str(e)}"
                                )
            
            return {
                "status": "completed",
                "penalties_applied": penalties_applied,
                "tasks_checked": tasks_checked
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in deadline penalty check: {str(e)}")
            raise
