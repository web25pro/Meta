"""Audit logging service layer"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.models.points_and_audit import AuditLog, AuditActionType
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Audit service for logging administrative actions"""
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        action: AuditActionType,
        resource_type: str,
        resource_id: uuid.UUID,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log an administrative action to the audit trail.
        
        This creates an immutable audit log entry for compliance and security purposes.
        All administrative actions (create, update, delete) should be logged.
        
        Args:
            db: Database session
            admin_user_id: ID of the admin performing the action
            action: Type of action performed (CREATE, UPDATE, DELETE, etc.)
            resource_type: Type of resource affected (Task, User, Submission, etc.)
            resource_id: ID of the affected resource
            changes: Optional dict containing before/after values for updates
            ip_address: Optional IP address of the request
            user_agent: Optional user agent of the request
            
        Returns:
            AuditLog: Created audit log entry
            
        Example:
            await AuditService.log_action(
                db=db,
                admin_user_id=current_user.id,
                action=AuditActionType.CREATE,
                resource_type="Task",
                resource_id=task.id,
                changes={"title": task.title, "deadline": str(task.deadline)},
                ip_address="192.168.1.1"
            )
        """
        try:
            # Create audit log entry
            audit_log = AuditLog(
                admin_user_id=admin_user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            await db.commit()
            await db.refresh(audit_log)
            
            logger.info(
                f"Audit log created: admin={admin_user_id}, action={action.value}, "
                f"resource_type={resource_type}, resource_id={resource_id}"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            # Don't rollback the main transaction - audit logging failure shouldn't break the operation
            # But we should log the error for investigation
            raise
    
    @staticmethod
    async def log_create(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        resource_type: str,
        resource_id: uuid.UUID,
        resource_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a CREATE action.
        
        Args:
            db: Database session
            admin_user_id: ID of the admin creating the resource
            resource_type: Type of resource created
            resource_id: ID of the created resource
            resource_data: Optional dict containing the created resource data
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            admin_user_id=admin_user_id,
            action=AuditActionType.CREATE,
            resource_type=resource_type,
            resource_id=resource_id,
            changes={"created": resource_data} if resource_data else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_update(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        resource_type: str,
        resource_id: uuid.UUID,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log an UPDATE action.
        
        Args:
            db: Database session
            admin_user_id: ID of the admin updating the resource
            resource_type: Type of resource updated
            resource_id: ID of the updated resource
            before: Optional dict containing values before update
            after: Optional dict containing values after update
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        changes = {}
        if before:
            changes["before"] = before
        if after:
            changes["after"] = after
            
        return await AuditService.log_action(
            db=db,
            admin_user_id=admin_user_id,
            action=AuditActionType.UPDATE,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes if changes else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_delete(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        resource_type: str,
        resource_id: uuid.UUID,
        resource_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a DELETE action.
        
        Args:
            db: Database session
            admin_user_id: ID of the admin deleting the resource
            resource_type: Type of resource deleted
            resource_id: ID of the deleted resource
            resource_data: Optional dict containing the deleted resource data
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            admin_user_id=admin_user_id,
            action=AuditActionType.DELETE,
            resource_type=resource_type,
            resource_id=resource_id,
            changes={"deleted": resource_data} if resource_data else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_approve(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        resource_type: str,
        resource_id: uuid.UUID,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log an APPROVE action (e.g., submission approval).
        
        Args:
            db: Database session
            admin_user_id: ID of the admin approving
            resource_type: Type of resource approved
            resource_id: ID of the approved resource
            metadata: Optional metadata about the approval
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            admin_user_id=admin_user_id,
            action=AuditActionType.APPROVE,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_reject(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        resource_type: str,
        resource_id: uuid.UUID,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a REJECT action (e.g., submission rejection).
        
        Args:
            db: Database session
            admin_user_id: ID of the admin rejecting
            resource_type: Type of resource rejected
            resource_id: ID of the rejected resource
            metadata: Optional metadata about the rejection
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            admin_user_id=admin_user_id,
            action=AuditActionType.REJECT,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_assign_points(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        user_id: uuid.UUID,
        amount: float,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log an ASSIGN_POINTS action (bonus points).
        
        Args:
            db: Database session
            admin_user_id: ID of the admin assigning points
            user_id: ID of the user receiving points
            amount: Amount of points assigned
            reason: Reason for assigning points
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            admin_user_id=admin_user_id,
            action=AuditActionType.ASSIGN_POINTS,
            resource_type="User",
            resource_id=user_id,
            changes={"amount": amount, "reason": reason},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_deduct_points(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        user_id: uuid.UUID,
        amount: float,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a DEDUCT_POINTS action (penalty points).
        
        Args:
            db: Database session
            admin_user_id: ID of the admin deducting points
            user_id: ID of the user losing points
            amount: Amount of points deducted
            reason: Reason for deducting points
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            admin_user_id=admin_user_id,
            action=AuditActionType.DEDUCT_POINTS,
            resource_type="User",
            resource_id=user_id,
            changes={"amount": amount, "reason": reason},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_reset_password(
        db: AsyncSession,
        admin_user_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a RESET_PASSWORD action.
        
        Args:
            db: Database session
            admin_user_id: ID of the admin resetting password
            user_id: ID of the user whose password was reset
            ip_address: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await AuditService.log_action(
            db=db,
            admin_user_id=admin_user_id,
            action=AuditActionType.RESET_PASSWORD,
            resource_type="User",
            resource_id=user_id,
            changes=None,  # Don't log password details
            ip_address=ip_address,
            user_agent=user_agent
        )
