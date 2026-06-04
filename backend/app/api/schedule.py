"""Schedule API endpoints"""
import uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import verify_token
from app.core.logging import get_logger
from app.core.rbac import Permission, has_permission, can_create_schedule_for_group
from app.models import User, UserRole, Schedule
from app.models.leaderboard_schedule_announcement import TargetGroup
from app.models.points_and_audit import AuditActionType
from app.services.audit_service import AuditService
from app.schemas.schedule import (
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleResponse,
    ScheduleListResponse
)
from sqlalchemy import select, or_, func

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/schedules", tags=["schedules"])
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid, user not found, or password changed after token issued
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Get user from database
    result = await db.execute(
        select(User).where(
            User.id == uuid.UUID(token_data.user_id),
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Validate token issuance time against password change
    if user.password_changed_at and token_data.iat < user.password_changed_at:
        raise HTTPException(status_code=401, detail="Session invalidated due to password change")
    
    return user


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    schedule_data: ScheduleCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    """
    Create a new schedule event with scope enforcement.
    
    **Validates: Requirements 7.1, 7.2, 7.3**
    
    - Overall_Admin can create schedules for any target_group (Team_Members, Ambassadors, All)
    - Ambassador_Admin can only create schedules for Ambassadors or All
    - Team_Member and Ambassador roles cannot create schedules
    
    Args:
        schedule_data: Schedule creation request data
        current_user: Current authenticated user
        db: Database session
        request: FastAPI request object for IP and user agent
        
    Returns:
        ScheduleResponse: Created schedule information
        
    Raises:
        HTTPException: 
            - 403 if user doesn't have permission to create schedules
            - 403 if admin tries to create schedule for unauthorized target_group
            - 400 if target_group is invalid
    """
    logger.info(
        f"User {current_user.id} ({current_user.role}) attempting to create schedule "
        f"for target_group={schedule_data.target_group}"
    )
    
    # Check if user has permission to create schedules
    if not has_permission(current_user.role, Permission.CREATE_SCHEDULE):
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to create schedule without permission"
        )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to create schedules"
        )
    
    # Validate target_group value
    valid_target_groups = ["Team_Members", "Ambassadors", "All"]
    if schedule_data.target_group not in valid_target_groups:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target_group. Must be one of: {valid_target_groups}"
        )
    
    # Check if admin can create schedule for the specified target_group
    if not can_create_schedule_for_group(current_user.role, schedule_data.target_group):
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to create schedule for unauthorized target_group={schedule_data.target_group}"
        )
        raise HTTPException(
            status_code=403,
            detail=f"You do not have permission to create schedules for {schedule_data.target_group}"
        )
    
    try:
        # Convert target_group string to TargetGroup enum
        target_group_enum = TargetGroup(schedule_data.target_group)
        
        # Create schedule
        schedule = Schedule(
            title=schedule_data.title,
            description=schedule_data.description,
            event_date=schedule_data.event_date,
            target_group=target_group_enum,
            created_by_id=current_user.id
        )
        
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)
        
        # Log audit trail
        await AuditService.log_create(
            db=db,
            admin_user_id=current_user.id,
            resource_type="Schedule",
            resource_id=schedule.id,
            resource_data={
                "title": schedule.title,
                "event_date": str(schedule.event_date),
                "target_group": schedule.target_group.value
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"Schedule {schedule.id} created successfully by user {current_user.id} "
            f"for target_group={schedule_data.target_group}"
        )
        
        return ScheduleResponse(
            id=schedule.id,
            title=schedule.title,
            description=schedule.description,
            event_date=schedule.event_date,
            target_group=schedule.target_group.value,
            created_by_id=schedule.created_by_id,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
        
    except ValueError as e:
        logger.error(f"Invalid target_group value: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target_group value: {schedule_data.target_group}"
        )
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create schedule"
        )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: uuid.UUID,
    schedule_data: ScheduleUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    """
    Update an existing schedule event with permission checks.
    
    **Validates: Requirement 7.4**
    
    - Overall_Admin can update any schedule
    - Ambassador_Admin can only update schedules for Ambassadors or All
    - Team_Member and Ambassador roles cannot update schedules
    - Supports updating title, description, event_date, and target_group
    
    Args:
        schedule_id: UUID of the schedule to update
        schedule_data: Schedule update request data
        current_user: Current authenticated user
        db: Database session
        request: FastAPI request object for IP and user agent
        
    Returns:
        ScheduleResponse: Updated schedule information
        
    Raises:
        HTTPException: 
            - 403 if user doesn't have permission to update schedules
            - 404 if schedule not found or already deleted
            - 403 if admin tries to update schedule to unauthorized target_group
            - 400 if target_group is invalid
    """
    logger.info(
        f"User {current_user.id} ({current_user.role}) attempting to update schedule {schedule_id}"
    )
    
    # Check if user has permission to update schedules
    if not has_permission(current_user.role, Permission.UPDATE_SCHEDULE):
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to update schedule without permission"
        )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update schedules"
        )
    
    # Fetch the schedule
    result = await db.execute(
        select(Schedule).where(
            Schedule.id == schedule_id,
            Schedule.deleted_at.is_(None)
        )
    )
    schedule = result.scalar_one_or_none()
    
    if schedule is None:
        logger.warning(f"Schedule {schedule_id} not found or already deleted")
        raise HTTPException(
            status_code=404,
            detail="Schedule not found"
        )
    
    # Capture before state for audit
    before_state = {
        "title": schedule.title,
        "description": schedule.description,
        "event_date": str(schedule.event_date),
        "target_group": schedule.target_group.value
    }
    
    try:
        # Update fields if provided
        if schedule_data.title is not None:
            schedule.title = schedule_data.title
        
        if schedule_data.description is not None:
            schedule.description = schedule_data.description
        
        if schedule_data.event_date is not None:
            schedule.event_date = schedule_data.event_date
        
        if schedule_data.target_group is not None:
            # Validate target_group value
            valid_target_groups = ["Team_Members", "Ambassadors", "All"]
            if schedule_data.target_group not in valid_target_groups:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid target_group. Must be one of: {valid_target_groups}"
                )
            
            # Check if admin can update schedule to the specified target_group
            if not can_create_schedule_for_group(current_user.role, schedule_data.target_group):
                logger.warning(
                    f"User {current_user.id} with role {current_user.role} "
                    f"attempted to update schedule to unauthorized target_group={schedule_data.target_group}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"You do not have permission to set target_group to {schedule_data.target_group}"
                )
            
            # Convert target_group string to TargetGroup enum
            schedule.target_group = TargetGroup(schedule_data.target_group)
        
        # Update the updated_at timestamp
        schedule.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(schedule)
        
        # Capture after state for audit
        after_state = {
            "title": schedule.title,
            "description": schedule.description,
            "event_date": str(schedule.event_date),
            "target_group": schedule.target_group.value
        }
        
        # Log audit trail
        await AuditService.log_update(
            db=db,
            admin_user_id=current_user.id,
            resource_type="Schedule",
            resource_id=schedule.id,
            before=before_state,
            after=after_state,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"Schedule {schedule.id} updated successfully by user {current_user.id}"
        )
        
        return ScheduleResponse(
            id=schedule.id,
            title=schedule.title,
            description=schedule.description,
            event_date=schedule.event_date,
            target_group=schedule.target_group.value,
            created_by_id=schedule.created_by_id,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except ValueError as e:
        logger.error(f"Invalid target_group value: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target_group value: {schedule_data.target_group}"
        )
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update schedule"
        )


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    """
    Soft delete a schedule event for audit trail.
    
    **Validates: Requirement 7.4**
    
    - Overall_Admin can delete any schedule
    - Ambassador_Admin can delete schedules for Ambassadors or All
    - Team_Member and Ambassador roles cannot delete schedules
    - Uses soft delete (sets deleted_at timestamp) for audit trail
    
    Args:
        schedule_id: UUID of the schedule to delete
        current_user: Current authenticated user
        db: Database session
        request: FastAPI request object for IP and user agent
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: 
            - 403 if user doesn't have permission to delete schedules
            - 404 if schedule not found or already deleted
            - 403 if Ambassador_Admin tries to delete Team_Members schedule
    """
    logger.info(
        f"User {current_user.id} ({current_user.role}) attempting to delete schedule {schedule_id}"
    )
    
    # Check if user has permission to delete schedules
    if not has_permission(current_user.role, Permission.DELETE_SCHEDULE):
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to delete schedule without permission"
        )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete schedules"
        )
    
    # Fetch the schedule
    result = await db.execute(
        select(Schedule).where(
            Schedule.id == schedule_id,
            Schedule.deleted_at.is_(None)
        )
    )
    schedule = result.scalar_one_or_none()
    
    if schedule is None:
        logger.warning(f"Schedule {schedule_id} not found or already deleted")
        raise HTTPException(
            status_code=404,
            detail="Schedule not found"
        )
    
    # Check if Ambassador_Admin is trying to delete a Team_Members schedule
    if current_user.role == UserRole.AMBASSADOR_ADMIN:
        if schedule.target_group == TargetGroup.TEAM_MEMBERS:
            logger.warning(
                f"Ambassador_Admin {current_user.id} attempted to delete "
                f"Team_Members schedule {schedule_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete schedules for Team_Members"
            )
    
    try:
        # Capture data for audit before deletion
        deleted_data = {
            "title": schedule.title,
            "event_date": str(schedule.event_date),
            "target_group": schedule.target_group.value
        }
        
        # Soft delete: set deleted_at timestamp
        schedule.deleted_at = datetime.utcnow()
        
        await db.commit()
        
        # Log audit trail
        await AuditService.log_delete(
            db=db,
            admin_user_id=current_user.id,
            resource_type="Schedule",
            resource_id=schedule_id,
            resource_data=deleted_data,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"Schedule {schedule.id} soft deleted successfully by user {current_user.id}"
        )
        
        return None
        
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete schedule"
        )



@router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
):
    """
    List schedules for the current user with visibility filtering.
    
    **Validates: Requirements 7.1, 7.5, 7.6**
    **Validates: Property 22 (Schedule Segregation)**
    **Validates: Property 26 (Schedule Visibility Filtering)**
    
    - Team_Members see schedules with target_group = Team_Members or All
    - Ambassadors see schedules with target_group = Ambassadors or All
    - Schedules are filtered based on user's user_type, not role
    - Supports pagination
    - Only returns non-deleted schedules
    
    Args:
        current_user: Current authenticated user
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        
    Returns:
        ScheduleListResponse: Paginated list of schedules visible to the user
    """
    logger.info(
        f"User {current_user.id} ({current_user.user_type}) requesting schedules "
        f"(page={page}, page_size={page_size})"
    )
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Build query with visibility filtering based on user_type
    # User sees schedules where target_group matches their user_type OR target_group is "All"
    if current_user.user_type.value == "Team_Member":
        target_group_filter = or_(
            Schedule.target_group == TargetGroup.TEAM_MEMBERS,
            Schedule.target_group == TargetGroup.ALL
        )
    else:  # Ambassador
        target_group_filter = or_(
            Schedule.target_group == TargetGroup.AMBASSADORS,
            Schedule.target_group == TargetGroup.ALL
        )
    
    # Query for schedules with filtering
    query = select(Schedule).where(
        Schedule.deleted_at.is_(None),
        target_group_filter
    ).order_by(Schedule.event_date.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(Schedule).where(
        Schedule.deleted_at.is_(None),
        target_group_filter
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    logger.info(
        f"Returning {len(schedules)} schedules for user {current_user.id} "
        f"(total={total}, page={page})"
    )
    
    # Convert to response format
    schedule_responses = [
        ScheduleResponse(
            id=schedule.id,
            title=schedule.title,
            description=schedule.description,
            event_date=schedule.event_date,
            target_group=schedule.target_group.value,
            created_by_id=schedule.created_by_id,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
        for schedule in schedules
    ]
    
    return ScheduleListResponse(
        schedules=schedule_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/admin", response_model=ScheduleListResponse)
async def list_all_schedules_admin(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
):
    """
    List all schedules without filtering (admin only).
    
    **Validates: Requirement 7.5**
    
    - Only accessible to Overall_Admin and Ambassador_Admin
    - Returns all schedules regardless of target_group
    - Supports pagination
    - Only returns non-deleted schedules
    
    Args:
        current_user: Current authenticated user
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        
    Returns:
        ScheduleListResponse: Paginated list of all schedules
        
    Raises:
        HTTPException: 403 if user is not an admin
    """
    logger.info(
        f"User {current_user.id} ({current_user.role}) requesting all schedules (admin) "
        f"(page={page}, page_size={page_size})"
    )
    
    # Check if user is an admin
    if current_user.role not in [UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]:
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to access admin schedule list"
        )
        raise HTTPException(
            status_code=403,
            detail="Only admins can access this endpoint"
        )
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query for all schedules (no filtering by target_group)
    query = select(Schedule).where(
        Schedule.deleted_at.is_(None)
    ).order_by(Schedule.event_date.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(Schedule).where(
        Schedule.deleted_at.is_(None)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    logger.info(
        f"Returning {len(schedules)} schedules for admin {current_user.id} "
        f"(total={total}, page={page})"
    )
    
    # Convert to response format
    schedule_responses = [
        ScheduleResponse(
            id=schedule.id,
            title=schedule.title,
            description=schedule.description,
            event_date=schedule.event_date,
            target_group=schedule.target_group.value,
            created_by_id=schedule.created_by_id,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
        for schedule in schedules
    ]
    
    return ScheduleListResponse(
        schedules=schedule_responses,
        total=total,
        page=page,
        page_size=page_size
    )
