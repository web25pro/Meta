"""Request/Response logging middleware"""
import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.core.security import verify_token

logger = get_logger(__name__)

# Sensitive headers to exclude from logs
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "x-auth-token",
}

# Sensitive query parameters to exclude from logs
SENSITIVE_QUERY_PARAMS = {
    "password",
    "token",
    "api_key",
    "secret",
}

# Sensitive body fields to exclude from logs
SENSITIVE_BODY_FIELDS = {
    "password",
    "old_password",
    "new_password",
    "token",
    "refresh_token",
    "access_token",
    "api_key",
    "secret",
}


def extract_user_id_from_request(request: Request) -> Optional[str]:
    """
    Extract user_id from JWT token in Authorization header.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: User ID if authenticated, None otherwise
    """
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            token_data = verify_token(token)
            if token_data:
                return token_data.user_id
    except Exception:
        # Silently fail - this is just for logging
        pass
    return None


def sanitize_headers(headers: dict) -> dict:
    """
    Remove sensitive headers from log output.
    
    Args:
        headers: Request/response headers
        
    Returns:
        dict: Sanitized headers
    """
    return {
        key: "***REDACTED***" if key.lower() in SENSITIVE_HEADERS else value
        for key, value in headers.items()
    }


def sanitize_query_params(query_params: dict) -> dict:
    """
    Remove sensitive query parameters from log output.
    
    Args:
        query_params: Query parameters
        
    Returns:
        dict: Sanitized query parameters
    """
    return {
        key: "***REDACTED***" if key.lower() in SENSITIVE_QUERY_PARAMS else value
        for key, value in query_params.items()
    }


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses.
    
    Logs:
    - user_id (if authenticated)
    - endpoint (path)
    - HTTP method
    - status code
    - response time (ms)
    - timestamp
    - client IP
    - user agent
    
    Excludes sensitive data:
    - Passwords
    - Tokens
    - Authorization headers
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: FastAPI response object
        """
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        
        # Extract user_id from JWT token
        user_id = extract_user_id_from_request(request)
        
        # Record start time
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Log request
        logger.info(
            "API Request",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": method,
                "path": path,
                "query_params": sanitize_query_params(query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "event_type": "api_request",
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "API Request Failed",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": method,
                    "path": path,
                    "status_code": 500,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "event_type": "api_response",
                },
                exc_info=True
            )
            raise
        
        # Calculate response time
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            "API Response",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "event_type": "api_response",
            }
        )
        
        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id
        
        return response
