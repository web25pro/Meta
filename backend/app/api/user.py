"""User API endpoints"""
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import verify_token
from app.core.logging import get_logger
from app.core.rbac import Permission, has_permission, check_permission
from app.models import User, UserRole, UserType
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Validates token expiration and password change invalidation:
    - If user changed password after token was issued, token is invalid
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await UserService.get_user_by_id(db, uuid.UUID(token_data.user_id))
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Validate token issuance time against password change
    # If password was changed after token was issued, invalidate token
    if user.password_changed_at and token_data.iat < user.password_changed_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalidated due to password change",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_optional)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Optional[User]:
    """
    Dependency to get the current authenticated user if available.
    """
    if credentials is None:
        return None
        
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        return None
    
    # Get user from database
    return await UserService.get_user_by_id(db, uuid.UUID(token_data.user_id))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Get current user profile.
    """
    return current_user


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_type: Optional[UserType] = None
):
    """
    List users with pagination (Admin only).
    """
    # Check if user is an admin
    if current_user.role not in [UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    users, total = await UserService.list_users(
        db=db,
        admin_role=current_user.role,
        page=page,
        page_size=page_size,
        user_type=user_type
    )
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Optional[User], Depends(get_optional_user)] = None
):
    """
    Create a new user.
    
    If current_user is provided and is an admin, allows creating any user type (within permissions).
    If no current_user is provided, only allows creating a user of type 'USER' with role 'USER'.
    """
    # If no authenticated user, only allow public registration of 'USER' role
    if current_user is None:
        if user_data.role != UserRole.USER or user_data.user_type != UserType.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public registration is only allowed for 'USER' role",
            )
        
        # For public registration, we use OVERALL_ADMIN role context in service
        # to bypass the can_manage_user check, as it's a self-registration
        try:
            user = await UserService.create_user(
                db=db,
                user_data=user_data,
                admin_role=UserRole.OVERALL_ADMIN
            )
            return user
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
            
    # If authenticated, check permissions as usual
    if not has_permission(current_user.role, Permission.CREATE_USER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    try:
        user = await UserService.create_user(
            db=db,
            user_data=user_data,
            admin_role=current_user.role
        )
        return user
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get user by ID (Admin only).
    """
    # Check if user is an admin
    if current_user.role not in [UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if admin can view this user
    from app.core.rbac import can_manage_user
    if not can_manage_user(current_user.role, user.user_type):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this user type",
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update user (Admin only).
    """
    # Check permission
    if not has_permission(current_user.role, Permission.UPDATE_USER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    try:
        user = await UserService.update_user(
            db=db,
            user_id=user_id,
            user_data=user_data,
            admin_role=current_user.role
        )
        return user
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Delete user (Admin only).
    """
    # Check permission
    if not has_permission(current_user.role, Permission.DELETE_USER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    try:
        await UserService.delete_user(
            db=db,
            user_id=user_id,
            admin_role=current_user.role
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
