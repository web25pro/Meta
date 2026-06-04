"""User service layer"""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models import User, UserRole, UserType
from app.core.security import hash_password
from app.core.rbac import can_manage_user
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """User service for business logic"""
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_data: UserCreate,
        admin_role: UserRole
    ) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            admin_role: Role of the admin creating the user
            
        Returns:
            User: Created user
            
        Raises:
            PermissionError: If admin cannot manage this user type
            ValueError: If email already exists
        """
        # Check if admin can manage this user type
        if not can_manage_user(admin_role, user_data.user_type):
            raise PermissionError(
                f"Admin with role {admin_role} cannot create users of type {user_data.user_type}"
            )
        
        # Check if email already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Create user
        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
            user_type=user_data.user_type,
            points=0.0
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User: User or None if not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User: User or None if not found
        """
        result = await db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_users(
        db: AsyncSession,
        admin_role: UserRole,
        page: int = 1,
        page_size: int = 20,
        user_type: Optional[UserType] = None
    ) -> tuple[List[User], int]:
        """
        List users with pagination.
        
        Args:
            db: Database session
            admin_role: Role of the admin listing users
            page: Page number (1-indexed)
            page_size: Number of users per page
            user_type: Filter by user type (optional)
            
        Returns:
            tuple: (list of users, total count)
        """
        # Build query
        query = select(User).where(User.deleted_at.is_(None))
        
        # Filter by user type if admin is Ambassador_Admin
        if admin_role == UserRole.AMBASSADOR_ADMIN:
            query = query.where(User.user_type == UserType.AMBASSADOR)
        elif user_type:
            query = query.where(User.user_type == user_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        user_data: UserUpdate,
        admin_role: UserRole
    ) -> User:
        """
        Update user.
        
        Args:
            db: Database session
            user_id: User ID
            user_data: User update data
            admin_role: Role of the admin updating the user
            
        Returns:
            User: Updated user
            
        Raises:
            PermissionError: If admin cannot manage this user type
            ValueError: If user not found or email already exists
        """
        # Get user
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if admin can manage this user type
        if not can_manage_user(admin_role, user.user_type):
            raise PermissionError(
                f"Admin with role {admin_role} cannot update users of type {user.user_type}"
            )
        
        # Update fields
        if user_data.name is not None:
            user.name = user_data.name
        
        if user_data.email is not None and user_data.email != user.email:
            # Check if new email already exists
            result = await db.execute(
                select(User).where(User.email == user_data.email, User.id != user_id)
            )
            if result.scalar_one_or_none():
                raise ValueError(f"User with email {user_data.email} already exists")
            user.email = user_data.email
        
        if user_data.role is not None:
            user.role = user_data.role
        
        if user_data.user_type is not None:
            user.user_type = user_data.user_type
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        admin_role: UserRole
    ) -> None:
        """
        Delete user (soft delete).
        
        Args:
            db: Database session
            user_id: User ID
            admin_role: Role of the admin deleting the user
            
        Raises:
            PermissionError: If admin cannot manage this user type
            ValueError: If user not found
        """
        # Get user
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if admin can manage this user type
        if not can_manage_user(admin_role, user.user_type):
            raise PermissionError(
                f"Admin with role {admin_role} cannot delete users of type {user.user_type}"
            )
        
        # Soft delete
        from datetime import datetime
        user.deleted_at = datetime.utcnow()
        
        await db.commit()
