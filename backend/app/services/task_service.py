"""Task service layer"""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.models import Task, TaskAssignment, User, UserRole, AssignedGroup, UserType
from app.core.rbac import can_create_task_for_group, Permission, has_permission
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Task service for business logic"""
    
    @staticmethod
    async def create_task(
        db: AsyncSession,
        task_data: TaskCreate,
        admin_id: uuid.UUID,
        admin_role: UserRole
    ) -> Task:
        """
        Create a new task.
        
        Args:
            db: Database session
            task_data: Task creation data
            admin_id: ID of the admin creating the task
            admin_role: Role of the admin creating the task
            
        Returns:
            Task: Created task
            
        Raises:
            PermissionError: If admin cannot create task for this group
            ValueError: If deadline is in the past
        """
        # Check if admin has permission to create tasks
        if not has_permission(admin_role, Permission.CREATE_TASK):
            raise PermissionError(f"Role {admin_role} does not have permission to create tasks")
        
        # Check if admin can create task for this group
        if not can_create_task_for_group(admin_role, task_data.assigned_to_group.value):
            raise PermissionError(
                f"Admin with role {admin_role} cannot create tasks for group {task_data.assigned_to_group}"
            )
        
        # Validate deadline is in the future
        if task_data.deadline <= datetime.utcnow():
            raise ValueError("Task deadline must be in the future")
        
        # Create task
        task = Task(
            title=task_data.title,
            description=task_data.description,
            assigned_to_group=task_data.assigned_to_group,
            deadline=task_data.deadline,
            point_value=task_data.point_value,
            created_by_id=admin_id
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        # Create task assignments for all users in the target group
        await TaskService._create_task_assignments(db, task)
        
        return task
    
    @staticmethod
    async def _create_task_assignments(
        db: AsyncSession,
        task: Task
    ) -> None:
        """
        Create task assignments for all users in the target group.
        
        Args:
            db: Database session
            task: Task to create assignments for
        """
        # Determine which users to assign based on group
        query = select(User).where(User.deleted_at.is_(None))
        
        if task.assigned_to_group == AssignedGroup.TEAM_MEMBERS:
            query = query.where(User.user_type == UserType.TEAM_MEMBER)
        elif task.assigned_to_group == AssignedGroup.AMBASSADORS:
            query = query.where(User.user_type == UserType.AMBASSADOR)
        # If AssignedGroup.ALL, no filter needed
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Create assignments
        for user in users:
            assignment = TaskAssignment(
                task_id=task.id,
                user_id=user.id
            )
            db.add(assignment)
        
        await db.commit()
    
    @staticmethod
    async def get_task_by_id(
        db: AsyncSession,
        task_id: uuid.UUID
    ) -> Optional[Task]:
        """
        Get task by ID.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            Task: Task or None if not found
        """
        result = await db.execute(
            select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        admin_role: UserRole,
        page: int = 1,
        page_size: int = 20,
        assigned_to_group: Optional[AssignedGroup] = None
    ) -> tuple[List[Task], int]:
        """
        List tasks with pagination.
        
        Args:
            db: Database session
            admin_role: Role of the admin listing tasks
            page: Page number (1-indexed)
            page_size: Number of tasks per page
            assigned_to_group: Filter by assigned group (optional)
            
        Returns:
            tuple: (list of tasks, total count)
        """
        # Build query
        query = select(Task).where(Task.deleted_at.is_(None))
        
        # Filter by assigned group if admin is Ambassador_Admin
        if admin_role == UserRole.AMBASSADOR_ADMIN:
            query = query.where(Task.assigned_to_group.in_([AssignedGroup.AMBASSADORS, AssignedGroup.ALL]))
        elif assigned_to_group:
            query = query.where(Task.assigned_to_group == assigned_to_group)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return list(tasks), total
    
    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: uuid.UUID,
        task_data: TaskUpdate,
        admin_role: UserRole
    ) -> Task:
        """
        Update task.
        
        Args:
            db: Database session
            task_id: Task ID
            task_data: Task update data
            admin_role: Role of the admin updating the task
            
        Returns:
            Task: Updated task
            
        Raises:
            PermissionError: If admin cannot update this task
            ValueError: If task not found or deadline is in the past
        """
        # Check if admin has permission to update tasks
        if not has_permission(admin_role, Permission.UPDATE_TASK):
            raise PermissionError(f"Role {admin_role} does not have permission to update tasks")
        
        # Get task
        task = await TaskService.get_task_by_id(db, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Check if admin can update this task
        if admin_role == UserRole.AMBASSADOR_ADMIN:
            if task.assigned_to_group not in [AssignedGroup.AMBASSADORS, AssignedGroup.ALL]:
                raise PermissionError(
                    f"Ambassador_Admin cannot update tasks for group {task.assigned_to_group}"
                )
        
        # Update fields
        if task_data.title is not None:
            task.title = task_data.title
        
        if task_data.description is not None:
            task.description = task_data.description
        
        if task_data.assigned_to_group is not None:
            # Check if admin can update to this group
            if not can_create_task_for_group(admin_role, task_data.assigned_to_group.value):
                raise PermissionError(
                    f"Admin with role {admin_role} cannot assign tasks to group {task_data.assigned_to_group}"
                )
            task.assigned_to_group = task_data.assigned_to_group
        
        if task_data.deadline is not None:
            if task_data.deadline <= datetime.utcnow():
                raise ValueError("Task deadline must be in the future")
            task.deadline = task_data.deadline
        
        if task_data.point_value is not None:
            task.point_value = task_data.point_value
        
        await db.commit()
        await db.refresh(task)
        
        return task
    
    @staticmethod
    async def delete_task(
        db: AsyncSession,
        task_id: uuid.UUID,
        admin_role: UserRole
    ) -> None:
        """
        Delete task (soft delete).
        
        Args:
            db: Database session
            task_id: Task ID
            admin_role: Role of the admin deleting the task
            
        Raises:
            PermissionError: If admin cannot delete this task
            ValueError: If task not found
        """
        # Check if admin has permission to delete tasks
        if not has_permission(admin_role, Permission.DELETE_TASK):
            raise PermissionError(f"Role {admin_role} does not have permission to delete tasks")
        
        # Get task
        task = await TaskService.get_task_by_id(db, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Check if admin can delete this task
        if admin_role == UserRole.AMBASSADOR_ADMIN:
            if task.assigned_to_group not in [AssignedGroup.AMBASSADORS, AssignedGroup.ALL]:
                raise PermissionError(
                    f"Ambassador_Admin cannot delete tasks for group {task.assigned_to_group}"
                )
        
        # Soft delete
        task.deleted_at = datetime.utcnow()
        
        await db.commit()
    
    @staticmethod
    async def get_user_tasks(
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Task], int]:
        """
        Get tasks assigned to a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of tasks per page
            
        Returns:
            tuple: (list of tasks, total count)
        """
        # Build query
        query = (
            select(Task)
            .join(TaskAssignment, Task.id == TaskAssignment.task_id)
            .where(
                TaskAssignment.user_id == user_id,
                Task.deleted_at.is_(None)
            )
        )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Task.deadline.asc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return list(tasks), total
