"""Announcement API endpoints"""
import uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import verify_token
from app.core.logging import get_logger
from app.core.rbac import Permission, has_permission, can_create_announcement_for_group
from app.models import User, UserRole, Announcement
from app.models.leaderboard_schedule_announcement import TargetGroup
from app.models.points_and_audit import AuditActionType
from app.services.audit_service import AuditService
from app.schemas.announcement import (
    AnnouncementCreateRequest,
    AnnouncementUpdateRequest,
    AnnouncementResponse,
    AnnouncementListResponse
)
from sqlalchemy import select, or_, func

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/announcements", tags=["announcements"])
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


@router.post("", response_model=AnnouncementResponse, status_code=201)
async def create_announcement(
    announcement_data: AnnouncementCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    """
    Create a new announcement with scope enforcement.
    
    **Validates: Requirements 8.1, 8.2**
    **Validates: Property 28 (Overall Admin Announcement Targeting)**
    **Validates: Property 29 (Ambassador Admin Announcement Restriction)**
    
    - Overall_Admin can create announcements for any target_group (Team_Members, Ambassadors, All)
    - Ambassador_Admin can only create announcements for Ambassadors or All
    - Team_Member and Ambassador roles cannot create announcements
    
    Args:
        announcement_data: Announcement creation request data
        current_user: Current authenticated user
        db: Database session
        request: FastAPI request object for IP and user agent
        
    Returns:
        AnnouncementResponse: Created announcement information
        
    Raises:
        HTTPException: 
            - 403 if user doesn't have permission to create announcements
            - 403 if admin tries to create announcement for unauthorized target_group
            - 400 if target_group is invalid
    """
    logger.info(
        f"User {current_user.id} ({current_user.role}) attempting to create announcement "
        f"for target_group={announcement_data.target_group}"
    )
    
    # Check if user has permission to create announcements
    if not has_permission(current_user.role, Permission.CREATE_ANNOUNCEMENT):
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to create announcement without permission"
        )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to create announcements"
        )
    
    # Validate target_group value
    valid_target_groups = ["Team_Members", "Ambassadors", "All"]
    if announcement_data.target_group not in valid_target_groups:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target_group. Must be one of: {valid_target_groups}"
        )
    
    # Check if admin can create announcement for the specified target_group
    if not can_create_announcement_for_group(current_user.role, announcement_data.target_group):
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to create announcement for unauthorized target_group={announcement_data.target_group}"
        )
        raise HTTPException(
            status_code=403,
            detail=f"You do not have permission to create announcements for {announcement_data.target_group}"
        )
    
    try:
        # Convert target_group string to TargetGroup enum
        target_group_enum = TargetGroup(announcement_data.target_group)
        
        # Create announcement
        announcement = Announcement(
            title=announcement_data.title,
            content=announcement_data.content,
            target_group=target_group_enum,
            created_by_id=current_user.id
        )
        
        db.add(announcement)
        await db.commit()
        await db.refresh(announcement)
        
        # Log audit trail
        await AuditService.log_create(
            db=db,
            admin_user_id=current_user.id,
            resource_type="Announcement",
            resource_id=announcement.id,
            resource_data={
                "title": announcement.title,
                "target_group": announcement.target_group.value
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"Announcement {announcement.id} created successfully by user {current_user.id} "
            f"for target_group={announcement_data.target_group}"
        )
        
        return AnnouncementResponse(
            id=announcement.id,
            title=announcement.title,
            content=announcement.content,
            target_group=announcement.target_group.value,
            created_by_id=announcement.created_by_id,
            created_at=announcement.created_at,
            updated_at=announcement.updated_at
        )
        
    except ValueError as e:
        logger.error(f"Invalid target_group value: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target_group value: {announcement_data.target_group}"
        )
    except Exception as e:
        logger.error(f"Error creating announcement: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create announcement"
        )


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: uuid.UUID,
    announcement_data: AnnouncementUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    """
    Update an existing announcement with permission checks.
    
    **Validates: Requirement 8.5**
    
    - Overall_Admin can update any announcement
    - Ambassador_Admin can only update announcements for Ambassadors or All
    - Team_Member and Ambassador roles cannot update announcements
    - Supports updating title, content, and target_group (all optional)
    - Maintains created_at for chronological ordering
    
    Args:
        announcement_id: UUID of the announcement to update
        announcement_data: Announcement update request data
        current_user: Current authenticated user
        db: Database session
        request: FastAPI request object for IP and user agent
        
    Returns:
        AnnouncementResponse: Updated announcement information
        
    Raises:
        HTTPException: 
            - 403 if user doesn't have permission to update announcements
            - 404 if announcement not found or already deleted
            - 403 if admin tries to update announcement to unauthorized target_group
            - 400 if target_group is invalid
    """
    logger.info(
        f"User {current_user.id} ({current_user.role}) attempting to update announcement {announcement_id}"
    )
    
    # Check if user has permission to update announcements
    if not has_permission(current_user.role, Permission.UPDATE_ANNOUNCEMENT):
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to update announcement without permission"
        )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update announcements"
        )
    
    # Fetch the announcement
    result = await db.execute(
        select(Announcement).where(
            Announcement.id == announcement_id,
            Announcement.deleted_at.is_(None)
        )
    )
    announcement = result.scalar_one_or_none()
    
    if announcement is None:
        logger.warning(f"Announcement {announcement_id} not found or already deleted")
        raise HTTPException(
            status_code=404,
            detail="Announcement not found"
        )
    
    # Capture before state for audit
    before_state = {
        "title": announcement.title,
        "content": announcement.content,
        "target_group": announcement.target_group.value
    }
    
    try:
        # Update fields if provided
        if announcement_data.title is not None:
            announcement.title = announcement_data.title
        
        if announcement_data.content is not None:
            announcement.content = announcement_data.content
        
        if announcement_data.target_group is not None:
            # Validate target_group value
            valid_target_groups = ["Team_Members", "Ambassadors", "All"]
            if announcement_data.target_group not in valid_target_groups:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid target_group. Must be one of: {valid_target_groups}"
                )
            
            # Check if admin can update announcement to the specified target_group
            if not can_create_announcement_for_group(current_user.role, announcement_data.target_group):
                logger.warning(
                    f"User {current_user.id} with role {current_user.role} "
                    f"attempted to update announcement to unauthorized target_group={announcement_data.target_group}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"You do not have permission to set target_group to {announcement_data.target_group}"
                )
            
            # Convert target_group string to TargetGroup enum
            announcement.target_group = TargetGroup(announcement_data.target_group)
        
        # Update the updated_at timestamp (created_at is maintained)
        announcement.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(announcement)
        
        # Capture after state for audit
        after_state = {
            "title": announcement.title,
            "content": announcement.content,
            "target_group": announcement.target_group.value
        }
        
        # Log audit trail
        await AuditService.log_update(
            db=db,
            admin_user_id=current_user.id,
            resource_type="Announcement",
            resource_id=announcement.id,
            before=before_state,
            after=after_state,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"Announcement {announcement.id} updated successfully by user {current_user.id}"
        )
        
        return AnnouncementResponse(
            id=announcement.id,
            title=announcement.title,
            content=announcement.content,
            target_group=announcement.target_group.value,
            created_by_id=announcement.created_by_id,
            created_at=announcement.created_at,
            updated_at=announcement.updated_at
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except ValueError as e:
        logger.error(f"Invalid target_group value: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target_group value: {announcement_data.target_group}"
        )
    except Exception as e:
        logger.error(f"Error updating announcement: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update announcement"
        )


@router.delete("/{announcement_id}", status_code=204)
async def delete_announcement(
    announcement_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    """
    Soft delete an announcement for audit trail.
    
    **Validates: Requirement 8.5**
    
    - Overall_Admin can delete any announcement
    - Ambassador_Admin can delete announcements for Ambassadors or All
    - Team_Member and Ambassador roles cannot delete announcements
    - Uses soft delete (sets deleted_at timestamp) for audit trail
    
    Args:
        announcement_id: UUID of the announcement to delete
        current_user: Current authenticated user
        db: Database session
        request: FastAPI request object for IP and user agent
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: 
            - 403 if user doesn't have permission to delete announcements
            - 404 if announcement not found or already deleted
            - 403 if Ambassador_Admin tries to delete Team_Members announcement
    """
    logger.info(
        f"User {current_user.id} ({current_user.role}) attempting to delete announcement {announcement_id}"
    )
    
    # Check if user has permission to delete announcements
    if not has_permission(current_user.role, Permission.DELETE_ANNOUNCEMENT):
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to delete announcement without permission"
        )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete announcements"
        )
    
    # Fetch the announcement
    result = await db.execute(
        select(Announcement).where(
            Announcement.id == announcement_id,
            Announcement.deleted_at.is_(None)
        )
    )
    announcement = result.scalar_one_or_none()
    
    if announcement is None:
        logger.warning(f"Announcement {announcement_id} not found or already deleted")
        raise HTTPException(
            status_code=404,
            detail="Announcement not found"
        )
    
    # Check if Ambassador_Admin is trying to delete a Team_Members announcement
    if current_user.role == UserRole.AMBASSADOR_ADMIN:
        if announcement.target_group == TargetGroup.TEAM_MEMBERS:
            logger.warning(
                f"Ambassador_Admin {current_user.id} attempted to delete "
                f"Team_Members announcement {announcement_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete announcements for Team_Members"
            )
    
    try:
        # Capture data for audit before deletion
        deleted_data = {
            "title": announcement.title,
            "target_group": announcement.target_group.value
        }
        
        # Soft delete: set deleted_at timestamp
        announcement.deleted_at = datetime.utcnow()
        
        await db.commit()
        
        # Log audit trail
        await AuditService.log_delete(
            db=db,
            admin_user_id=current_user.id,
            resource_type="Announcement",
            resource_id=announcement_id,
            resource_data=deleted_data,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"Announcement {announcement.id} soft deleted successfully by user {current_user.id}"
        )
        
        return None
        
    except Exception as e:
        logger.error(f"Error deleting announcement: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete announcement"
        )


@router.get("", response_model=AnnouncementListResponse)
async def list_announcements(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
):
    """
    List announcements for the current user with visibility filtering.
    
    **Validates: Requirements 8.3, 8.4**
    **Validates: Property 30 (Announcement Visibility Filtering)**
    **Validates: Property 31 (Announcement Chronological Ordering)**
    
    - Team_Members see announcements with target_group = Team_Members or All
    - Ambassadors see announcements with target_group = Ambassadors or All
    - Announcements are filtered based on user's user_type, not role
    - Announcements are ordered by created_at descending (newest first)
    - Supports pagination
    - Only returns non-deleted announcements
    
    Args:
        current_user: Current authenticated user
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        
    Returns:
        AnnouncementListResponse: Paginated list of announcements visible to the user
    """
    logger.info(
        f"User {current_user.id} ({current_user.user_type}) requesting announcements "
        f"(page={page}, page_size={page_size})"
    )
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Build query with visibility filtering based on user_type
    # User sees announcements where target_group matches their user_type OR target_group is "All"
    if current_user.user_type.value == "Team_Member":
        target_group_filter = or_(
            Announcement.target_group == TargetGroup.TEAM_MEMBERS,
            Announcement.target_group == TargetGroup.ALL
        )
    else:  # Ambassador
        target_group_filter = or_(
            Announcement.target_group == TargetGroup.AMBASSADORS,
            Announcement.target_group == TargetGroup.ALL
        )
    
    # Query for announcements with filtering
    # Order by created_at descending (newest first) per Requirement 8.4
    query = select(Announcement).where(
        Announcement.deleted_at.is_(None),
        target_group_filter
    ).order_by(Announcement.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(Announcement).where(
        Announcement.deleted_at.is_(None),
        target_group_filter
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    announcements = result.scalars().all()
    
    logger.info(
        f"Returning {len(announcements)} announcements for user {current_user.id} "
        f"(total={total}, page={page})"
    )
    
    # Convert to response format
    announcement_responses = [
        AnnouncementResponse(
            id=announcement.id,
            title=announcement.title,
            content=announcement.content,
            target_group=announcement.target_group.value,
            created_by_id=announcement.created_by_id,
            created_at=announcement.created_at,
            updated_at=announcement.updated_at
        )
        for announcement in announcements
    ]
    
    return AnnouncementListResponse(
        announcements=announcement_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/admin", response_model=AnnouncementListResponse)
async def list_all_announcements_admin(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
):
    """
    List all announcements without filtering (admin only).
    
    **Validates: Requirements 8.1, 8.2**
    
    - Only accessible to Overall_Admin and Ambassador_Admin
    - Returns all announcements regardless of target_group
    - Announcements are ordered by created_at descending (newest first)
    - Supports pagination
    - Only returns non-deleted announcements
    
    Args:
        current_user: Current authenticated user
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        
    Returns:
        AnnouncementListResponse: Paginated list of all announcements
        
    Raises:
        HTTPException: 403 if user is not an admin
    """
    logger.info(
        f"User {current_user.id} ({current_user.role}) requesting all announcements (admin) "
        f"(page={page}, page_size={page_size})"
    )
    
    # Check if user is an admin
    if current_user.role not in [UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]:
        logger.warning(
            f"User {current_user.id} with role {current_user.role} "
            f"attempted to access admin announcement list"
        )
        raise HTTPException(
            status_code=403,
            detail="Only admins can access this endpoint"
        )
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query for all announcements (no filtering by target_group)
    # Order by created_at descending (newest first)
    query = select(Announcement).where(
        Announcement.deleted_at.is_(None)
    ).order_by(Announcement.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(Announcement).where(
        Announcement.deleted_at.is_(None)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    announcements = result.scalars().all()
    
    logger.info(
        f"Returning {len(announcements)} announcements for admin {current_user.id} "
        f"(total={total}, page={page})"
    )
    
    # Convert to response format
    announcement_responses = [
        AnnouncementResponse(
            id=announcement.id,
            title=announcement.title,
            content=announcement.content,
            target_group=announcement.target_group.value,
            created_by_id=announcement.created_by_id,
            created_at=announcement.created_at,
            updated_at=announcement.updated_at
        )
        for announcement in announcements
    ]
    
    return AnnouncementListResponse(
        announcements=announcement_responses,
        total=total,
        page=page,
        page_size=page_size
    )
