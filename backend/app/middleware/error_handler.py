"""Custom error handler middleware for FastAPI"""
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.core.sentry import capture_exception, set_user_context, set_tag
from app.core.exceptions import APIException

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle uncaught exceptions and send them to Sentry.
    
    Features:
    - Catches all unhandled exceptions
    - Logs errors with full context
    - Sends errors to Sentry with user context
    - Returns standardized error responses
    - Handles database errors gracefully
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle any exceptions.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: FastAPI response object
        """
        try:
            # Extract user context for Sentry
            user_id = self._extract_user_id(request)
            if user_id:
                set_user_context(user_id=user_id)
            
            # Add request context tags
            set_tag("endpoint", request.url.path)
            set_tag("method", request.method)
            
            # Process request
            response = await call_next(request)
            return response
        
        except APIException as e:
            # Custom API exceptions with standardized format
            logger.warning(
                f"API exception: {e.code}",
                extra={
                    "error_code": e.code,
                    "message": e.message,
                    "status_code": e.status_code,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "details": e.details,
                }
            )
            
            # Only send to Sentry if it's a server error (5xx)
            if e.status_code >= 500:
                capture_exception(
                    e,
                    tags={
                        "error_category": "api_exception",
                        "error_code": e.code,
                        "endpoint": request.url.path,
                    }
                )
            
            return JSONResponse(
                status_code=e.status_code,
                content=e.to_dict()
            )
        
        except StarletteHTTPException as e:
            # Handle Starlette/FastAPI HTTPException
            logger.warning(
                f"HTTP exception: {e.status_code}",
                extra={
                    "status_code": e.status_code,
                    "detail": e.detail,
                    "endpoint": request.url.path,
                    "method": request.method,
                }
            )
            
            # Convert to standardized format
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": {
                        "code": self._get_error_code_from_status(e.status_code),
                        "message": str(e.detail) if e.detail else "An error occurred",
                        "details": {}
                    }
                }
            )
            
        except SQLAlchemyError as e:
            # Database errors
            logger.error(
                "Database error occurred",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "endpoint": request.url.path,
                    "method": request.method,
                },
                exc_info=True
            )
            
            # Send to Sentry
            capture_exception(
                e,
                tags={
                    "error_category": "database",
                    "endpoint": request.url.path,
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "success": False,
                    "error": {
                        "code": "DATABASE_ERROR",
                        "message": "A database error occurred. Please try again later.",
                        "details": {}
                    }
                }
            )
            
        except Exception as e:
            # All other unhandled exceptions
            logger.error(
                "Unhandled exception occurred",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc(),
                },
                exc_info=True
            )
            
            # Send to Sentry
            capture_exception(
                e,
                tags={
                    "error_category": "unhandled",
                    "endpoint": request.url.path,
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": f"An unexpected error occurred: {type(e).__name__}",
                        "details": {"error_type": type(e).__name__, "error_msg": str(e)}
                    }
                }
            )
    
    def _get_error_code_from_status(self, status_code: int) -> str:
        """
        Get error code from HTTP status code.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            str: Error code string
        """
        error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }
        return error_codes.get(status_code, "UNKNOWN_ERROR")
    
    def _extract_user_id(self, request: Request) -> str | None:
        """
        Extract user_id from JWT token in Authorization header.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Optional[str]: User ID if authenticated, None otherwise
        """
        try:
            from app.core.security import verify_token
            
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                token_data = verify_token(token)
                if token_data:
                    return token_data.user_id
        except Exception:
            # Silently fail - this is just for context
            pass
        return None
