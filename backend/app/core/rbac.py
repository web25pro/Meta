"""Role-Based Access Control (RBAC) utilities"""
from typing import List, Optional
from enum import Enum

from app.models import UserRole, UserType


class Permission(str, Enum):
    """Permission enumeration"""
    # User management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    RESET_PASSWORD = "reset_password"
    
    # Task management
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    
    # Submission management
    APPROVE_SUBMISSION = "approve_submission"
    REJECT_SUBMISSION = "reject_submission"
    
    # Points management
    ASSIGN_POINTS = "assign_points"
    DEDUCT_POINTS = "deduct_points"
    
    # Announcements
    CREATE_ANNOUNCEMENT = "create_announcement"
    UPDATE_ANNOUNCEMENT = "update_announcement"
    DELETE_ANNOUNCEMENT = "delete_announcement"
    
    # Schedules
    CREATE_SCHEDULE = "create_schedule"
    UPDATE_SCHEDULE = "update_schedule"
    DELETE_SCHEDULE = "delete_schedule"
    
    # Analytics
    VIEW_ANALYTICS = "view_analytics"


# Permission matrix: role -> list of permissions
PERMISSION_MATRIX = {
    UserRole.OVERALL_ADMIN: [
        Permission.CREATE_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.RESET_PASSWORD,
        Permission.CREATE_TASK,
        Permission.UPDATE_TASK,
        Permission.DELETE_TASK,
        Permission.APPROVE_SUBMISSION,
        Permission.REJECT_SUBMISSION,
        Permission.ASSIGN_POINTS,
        Permission.DEDUCT_POINTS,
        Permission.CREATE_ANNOUNCEMENT,
        Permission.UPDATE_ANNOUNCEMENT,
        Permission.DELETE_ANNOUNCEMENT,
        Permission.CREATE_SCHEDULE,
        Permission.UPDATE_SCHEDULE,
        Permission.DELETE_SCHEDULE,
        Permission.VIEW_ANALYTICS,
    ],
    UserRole.AMBASSADOR_ADMIN: [
        Permission.CREATE_USER,  # Only ambassadors
        Permission.UPDATE_USER,  # Only ambassadors
        Permission.DELETE_USER,  # Only ambassadors
        Permission.RESET_PASSWORD,  # Only ambassadors
        Permission.CREATE_TASK,  # Only for ambassadors
        Permission.UPDATE_TASK,  # Only for ambassadors
        Permission.DELETE_TASK,  # Only for ambassadors
        Permission.APPROVE_SUBMISSION,  # Only ambassador submissions
        Permission.REJECT_SUBMISSION,  # Only ambassador submissions
        Permission.ASSIGN_POINTS,  # Only for ambassadors
        Permission.DEDUCT_POINTS,  # Only for ambassadors
        Permission.CREATE_ANNOUNCEMENT,  # Only for ambassadors
        Permission.UPDATE_ANNOUNCEMENT,  # Only for ambassadors
        Permission.DELETE_ANNOUNCEMENT,  # Only for ambassadors
        Permission.CREATE_SCHEDULE,  # Only for ambassadors
        Permission.UPDATE_SCHEDULE,  # Only for ambassadors
        Permission.DELETE_SCHEDULE,  # Only for ambassadors
    ],
    UserRole.TEAM_MEMBER: [],
    UserRole.AMBASSADOR: [],
    UserRole.USER: [],
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.
    
    Args:
        role: User role
        permission: Permission to check
        
    Returns:
        bool: True if role has permission, False otherwise
    """
    return permission in PERMISSION_MATRIX.get(role, [])


def check_permission(role: UserRole, permission: Permission) -> None:
    """
    Check if a role has a specific permission, raise exception if not.
    
    Args:
        role: User role
        permission: Permission to check
        
    Raises:
        PermissionError: If role doesn't have permission
    """
    if not has_permission(role, permission):
        raise PermissionError(f"Role {role} does not have permission {permission}")


def can_manage_user(admin_role: UserRole, target_user_type: UserType) -> bool:
    """
    Check if an admin can manage a specific user type.
    
    Args:
        admin_role: Admin role
        target_user_type: Target user type
        
    Returns:
        bool: True if admin can manage user type, False otherwise
    """
    if admin_role == UserRole.OVERALL_ADMIN:
        return True
    elif admin_role == UserRole.AMBASSADOR_ADMIN:
        return target_user_type == UserType.AMBASSADOR
    else:
        return False


def can_create_task_for_group(admin_role: UserRole, target_group: str) -> bool:
    """
    Check if an admin can create tasks for a specific group.
    
    Args:
        admin_role: Admin role
        target_group: Target group (Team_Members, Ambassadors, All)
        
    Returns:
        bool: True if admin can create task for group, False otherwise
    """
    if admin_role == UserRole.OVERALL_ADMIN:
        return True
    elif admin_role == UserRole.AMBASSADOR_ADMIN:
        return target_group in ["Ambassadors", "All"]
    else:
        return False


def can_create_announcement_for_group(admin_role: UserRole, target_group: str) -> bool:
    """
    Check if an admin can create announcements for a specific group.
    
    Args:
        admin_role: Admin role
        target_group: Target group (Team_Members, Ambassadors, All)
        
    Returns:
        bool: True if admin can create announcement for group, False otherwise
    """
    if admin_role == UserRole.OVERALL_ADMIN:
        return True
    elif admin_role == UserRole.AMBASSADOR_ADMIN:
        return target_group in ["Ambassadors", "All"]
    else:
        return False


def can_create_schedule_for_group(admin_role: UserRole, target_group: str) -> bool:
    """
    Check if an admin can create schedules for a specific group.
    
    Args:
        admin_role: Admin role
        target_group: Target group (Team_Members, Ambassadors, All)
        
    Returns:
        bool: True if admin can create schedule for group, False otherwise
    """
    if admin_role == UserRole.OVERALL_ADMIN:
        return True
    elif admin_role == UserRole.AMBASSADOR_ADMIN:
        return target_group in ["Ambassadors", "All"]
    else:
        return False
