"""Task API endpoints"""
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.rbac import Permission, has_permission
from app.models import User, UserRole, AssignedGroup
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from app.api.user import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create a new task (Admin only).
    """
    try:
        task = await TaskService.create_task(
            db=db,
            task_data=task_data,
            admin_id=current_user.id,
            admin_role=current_user.role
        )
        return task
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    assigned_to_group: Optional[AssignedGroup] = None
):
    """
    List all tasks with pagination (Admin only).
    """
    if current_user.role not in [UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    tasks, total = await TaskService.list_tasks(
        db=db,
        admin_role=current_user.role,
        page=page,
        page_size=page_size,
        assigned_to_group=assigned_to_group
    )
    
    return {
        "tasks": tasks,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/my-tasks", response_model=TaskListResponse)
async def get_my_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get tasks assigned to the current user.
    """
    tasks, total = await TaskService.get_user_tasks(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return {
        "tasks": tasks,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get task details by ID.
    """
    task = await TaskService.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # Non-admins can only see tasks assigned to them
    if current_user.role not in [UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]:
        # Check if task is assigned to user's group
        from app.models import UserType
        if task.assigned_to_group == AssignedGroup.ALL:
            pass
        elif task.assigned_to_group == AssignedGroup.TEAM_MEMBERS and current_user.user_type != UserType.TEAM_MEMBER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        elif task.assigned_to_group == AssignedGroup.AMBASSADORS and current_user.user_type != UserType.AMBASSADOR:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    task_data: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update task (Admin only).
    """
    try:
        task = await TaskService.update_task(
            db=db,
            task_id=task_id,
            task_data=task_data,
            admin_role=current_user.role
        )
        return task
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Delete task (Admin only).
    """
    try:
        await TaskService.delete_task(
            db=db,
            task_id=task_id,
            admin_role=current_user.role
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
