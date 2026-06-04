"""API endpoints for community user operations"""
import math
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.community import (
    CommunityUserRegisterRequest,
    CommunityUserResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    LoginRequest,
    LoginResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    ReferralCodeResponse
)
from app.schemas.public_task import (
    TaskCategory,
    PublicTaskSummary,
    PublicTaskDetail,
    PaginatedTaskResponse,
)
from app.schemas.submission import (
    SubmissionResponse,
    SubmissionListResponse,
    SubmissionCreate,
    SubmissionFileData,
)
from app.services.community_service import (
    create_community_user,
    generate_verification_token,
    verify_verification_token,
    generate_password_reset_token,
    verify_password_reset_token,
    get_user_by_email
)
from app.services.public_task_service import (
    get_public_tasks,
    get_task_by_id,
)
from app.core.email import send_verification_email, send_password_reset_email
from app.services.submission_service import SubmissionService
from app.core.security import verify_password, create_access_token, create_refresh_token, hash_password
from app.models.user import User
from app.api.user import get_current_user

router = APIRouter(prefix="/api/v1/community", tags=["Community"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=CommunityUserResponse, status_code=status.HTTP_201_CREATED)
async def register_community_user(
    data: CommunityUserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new community user account.
    
    - **email**: Valid email address (unique)
    - **password**: Minimum 8 characters with complexity requirements
    - **username**: 3-20 characters, alphanumeric + underscore (unique)
    - **referral_code**: Optional 8-character referral code from existing user
    
    Returns the created user with email_verified=False.
    A verification email will be sent to the provided email address.
    """
    registration_ip = get_client_ip(request)
    
    user = await create_community_user(
        db=db,
        email=data.email,
        password=data.password,
        username=data.username,
        registration_ip=registration_ip,
        referral_code=data.referral_code
    )
    
    if user.email_verification_token:
        try:
            await send_verification_email(user.email, user.email_verification_token)
        except Exception:
            # If email delivery fails, still return the user object
            pass
    
    return user


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user's email address using the token sent via email.
    
    - **token**: JWT token from verification email
    
    Returns success message if verification is successful.
    """
    user_id = verify_verification_token(data.token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_VERIFICATION_TOKEN"
        )
    
    # Get user and update email_verified
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="USER_NOT_FOUND"
        )
    
    if user.email_verified:
        return EmailVerificationResponse(
            message="Email already verified",
            email_verified=True
        )
    
    user.email_verified = True
    user.email_verification_token = None
    await db.commit()
    
    return EmailVerificationResponse(
        message="Email verified successfully",
        email_verified=True
    )


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification_email(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend email verification link.
    
    - **email**: User's email address
    
    Returns success message (even if email doesn't exist for security).
    """
    user = await get_user_by_email(db, email)
    
    # Always return success for security (don't reveal if email exists)
    if not user:
        return {"message": "If the email exists, a verification link has been sent"}
    
    if user.email_verified:
        return {"message": "Email is already verified"}

    if not user.email_verification_token:
        user.email_verification_token = generate_verification_token(user.id)
    user.email_verification_sent_at = datetime.utcnow()
    await db.commit()

    try:
        await send_verification_email(user.email, user.email_verification_token)
    except Exception:
        pass

    return {"message": "Verification email sent successfully"}


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token, refresh token, and user data.
    """
    user = await get_user_by_email(db, data.email)
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACCOUNT_SUSPENDED"
        )
    
    # Update last login IP
    user.last_login_ip = get_client_ip(request)
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        user_type=user.user_type.value
    )
    refresh_token = create_refresh_token(user_id=str(user.id))
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=CommunityUserResponse.model_validate(user)
    )


@router.post("/password-reset-request", response_model=PasswordResetResponse)
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset link.
    
    - **email**: User's email address
    
    Returns success message (even if email doesn't exist for security).
    """
    user = await get_user_by_email(db, data.email)
    
    # Always return success for security (don't reveal if email exists)
    if not user:
        return PasswordResetResponse(
            message="If the email exists, a password reset link has been sent"
        )
    
    reset_token = generate_password_reset_token(user.id)
    try:
        await send_password_reset_email(user.email, reset_token)
    except Exception:
        pass
    
    return PasswordResetResponse(
        message="Password reset link sent successfully"
    )


@router.post("/password-reset-confirm", response_model=PasswordResetConfirmResponse)
async def confirm_password_reset(
    data: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with token and new password.
    
    - **token**: JWT token from password reset email
    - **new_password**: New password (min 8 characters with complexity)
    
    Returns success message if password is reset successfully.
    """
    user_id = verify_password_reset_token(data.token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_RESET_TOKEN"
        )
    
    # Get user and update password
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="USER_NOT_FOUND"
        )
    
    # Hash new password
    user.password_hash = hash_password(data.new_password)
    user.password_changed_at = datetime.utcnow()
    await db.commit()
    
    return PasswordResetConfirmResponse(
        message="Password reset successfully"
    )


@router.get("/tasks", response_model=PaginatedTaskResponse)
async def list_public_tasks(
    category: Optional[TaskCategory] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List public tasks available to community users."""
    tasks, total = await get_public_tasks(
        db=db,
        category=category,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedTaskResponse(
        tasks=tasks,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/tasks/{task_id}", response_model=PublicTaskDetail)
async def get_public_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed public task information."""
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TASK_NOT_FOUND")
    return task


@router.post("/tasks/{task_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_public_task(
    task_id: uuid.UUID,
    content: str = Form(..., min_length=10),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit a public task with optional file attachments."""
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TASK_NOT_FOUND")
    if not task.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TASK_NOT_ACTIVE")
    if not current_user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="EMAIL_NOT_VERIFIED")
    if task.deadline < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="DEADLINE_PASSED")
    if task.max_submissions and task.current_submissions >= task.max_submissions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SUBMISSION_LIMIT_REACHED")

    file_items: list[SubmissionFileData] = []
    if files:
        for file in files:
            file_contents = await file.read()
            if len(file_contents) > 50 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"FILE_TOO_LARGE: {file.filename} exceeds 50MB"
                )
            extension = file.filename.split('.')[-1].lower() if file.filename else ''
            allowed_extensions = {
                'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt', 'mp4', 'mov'
            }
            if extension not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"FILE_TYPE_NOT_ALLOWED: Allowed types are {', '.join(sorted(allowed_extensions))}"
                )
            file_items.append(SubmissionFileData(
                file_name=file.filename or "upload",
                file_data=file_contents,
                mime_type=file.content_type or "application/octet-stream"
            ))

    submission_payload = SubmissionCreate(
        task_id=task_id,
        content=content,
        files=file_items or None
    )

    try:
        submission = await SubmissionService.create_submission(
            db=db,
            submission_data=submission_payload,
            user_id=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    task.current_submissions += 1
    await db.commit()
    await db.refresh(submission)
    return submission


@router.get("/submissions", response_model=SubmissionListResponse)
async def list_my_submissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List submissions made by the authenticated community user."""
    submissions, total = await SubmissionService.get_user_submissions(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return SubmissionListResponse(
        submissions=submissions,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/referral-code", response_model=ReferralCodeResponse)
async def get_referral_code(
    current_user: User = Depends(get_current_user)
):
    """
    Get authenticated user's referral code and link.
    
    Requires authentication.
    
    Returns referral code and shareable link.
    """
    referral_link = f"{settings.SITE_BASE_URL}/register?ref={current_user.referral_code}"
    
    return ReferralCodeResponse(
        referral_code=current_user.referral_code,
        referral_link=referral_link
    )
