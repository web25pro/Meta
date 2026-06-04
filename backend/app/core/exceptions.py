"""Custom exception classes for standardized error responses"""
from typing import Optional, Dict, Any
from fastapi import status


class APIException(Exception):
    """
    Base exception class for API errors.
    
    All custom exceptions should inherit from this class to ensure
    consistent error response formatting.
    """
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API exception.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary format for JSON response.
        
        Returns:
            Dict containing success=False and error details
        """
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


class BadRequestException(APIException):
    """
    Exception for 400 Bad Request errors.
    
    Use when the request is malformed or contains invalid data.
    """
    
    def __init__(
        self,
        message: str = "Bad request",
        code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class UnauthorizedException(APIException):
    """
    Exception for 401 Unauthorized errors.
    
    Use when authentication is required but missing or invalid.
    """
    
    def __init__(
        self,
        message: str = "Authentication required",
        code: str = "UNAUTHORIZED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class ForbiddenException(APIException):
    """
    Exception for 403 Forbidden errors.
    
    Use when the user is authenticated but lacks permission.
    """
    
    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        code: str = "FORBIDDEN",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class NotFoundException(APIException):
    """
    Exception for 404 Not Found errors.
    
    Use when a requested resource does not exist.
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ConflictException(APIException):
    """
    Exception for 409 Conflict errors.
    
    Use when the request conflicts with the current state (e.g., duplicate submission).
    """
    
    def __init__(
        self,
        message: str = "Request conflicts with current state",
        code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class ValidationException(APIException):
    """
    Exception for 422 Unprocessable Entity errors.
    
    Use when request validation fails.
    """
    
    def __init__(
        self,
        message: str = "Request validation failed",
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class RateLimitException(APIException):
    """
    Exception for 429 Too Many Requests errors.
    
    Use when rate limit is exceeded.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        code: str = "RATE_LIMIT_EXCEEDED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class InternalServerException(APIException):
    """
    Exception for 500 Internal Server Error.
    
    Use when an unexpected error occurs.
    """
    
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ServiceUnavailableException(APIException):
    """
    Exception for 503 Service Unavailable errors.
    
    Use when a required service (database, cache, etc.) is unavailable.
    """
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        code: str = "SERVICE_UNAVAILABLE",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )
