"""Sentry error tracking and performance monitoring integration"""
import logging
from typing import Optional
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry SDK for error tracking and performance monitoring.
    
    Features:
    - Error tracking with automatic exception capture
    - Performance monitoring (response time tracking)
    - Request context (user, endpoint, method)
    - Release tracking for deployment correlation
    - Environment-based filtering
    
    Alerts configured in Sentry dashboard:
    - Error rate > 1%
    - Response time p95 > 1 second
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return
    
    # Determine environment
    environment = settings.SENTRY_ENVIRONMENT or settings.APP_ENV
    
    # Configure logging integration
    # Capture logs at ERROR level and above
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors and above as events
    )
    
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=environment,
            release=f"{settings.APP_NAME}@{settings.API_VERSION}",
            
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                logging_integration,
            ],
            
            # Performance Monitoring
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            
            # Error Sampling
            # Send all errors (100%)
            sample_rate=1.0,
            
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII by default
            max_breadcrumbs=50,
            
            # Before send hook to filter sensitive data
            before_send=before_send_filter,
            
            # Before send transaction hook for performance data
            before_send_transaction=before_send_transaction_filter,
        )
        
        logger.info(
            "Sentry initialized successfully",
            extra={
                "environment": environment,
                "release": f"{settings.APP_NAME}@{settings.API_VERSION}",
                "traces_sample_rate": settings.SENTRY_TRACES_SAMPLE_RATE,
            }
        )
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)


def before_send_filter(event: dict, hint: dict) -> Optional[dict]:
    """
    Filter and sanitize events before sending to Sentry.
    
    Removes sensitive data from:
    - Request headers (Authorization, Cookie)
    - Request body (passwords, tokens)
    - Query parameters (api_key, secret)
    
    Args:
        event: Sentry event dictionary
        hint: Additional context about the event
        
    Returns:
        Optional[dict]: Filtered event or None to drop the event
    """
    # Sanitize request data
    if "request" in event:
        request = event["request"]
        
        # Sanitize headers
        if "headers" in request:
            sensitive_headers = {"authorization", "cookie", "x-api-key", "x-auth-token"}
            for header in sensitive_headers:
                if header in request["headers"]:
                    request["headers"][header] = "***REDACTED***"
        
        # Sanitize query string
        if "query_string" in request:
            sensitive_params = {"password", "token", "api_key", "secret"}
            query_string = request.get("query_string", "")
            for param in sensitive_params:
                if param in query_string.lower():
                    request["query_string"] = "***REDACTED***"
                    break
        
        # Sanitize request body
        if "data" in request and isinstance(request["data"], dict):
            sensitive_fields = {
                "password", "old_password", "new_password",
                "token", "refresh_token", "access_token",
                "api_key", "secret"
            }
            for field in sensitive_fields:
                if field in request["data"]:
                    request["data"][field] = "***REDACTED***"
    
    # Sanitize user data
    if "user" in event:
        # Keep user_id but remove email and other PII
        user = event["user"]
        if "email" in user:
            user["email"] = "***REDACTED***"
        if "username" in user:
            user["username"] = "***REDACTED***"
    
    return event


def before_send_transaction_filter(event: dict, hint: dict) -> Optional[dict]:
    """
    Filter performance transactions before sending to Sentry.
    
    Can be used to:
    - Drop low-priority transactions
    - Sample high-volume endpoints differently
    - Add custom tags or context
    
    Args:
        event: Sentry transaction event
        hint: Additional context
        
    Returns:
        Optional[dict]: Filtered event or None to drop
    """
    # Add custom tags for better filtering in Sentry
    if "transaction" in event:
        transaction_name = event["transaction"]
        
        # Tag health check endpoints
        if transaction_name in ["/health", "/", "/docs", "/openapi.json"]:
            if "tags" not in event:
                event["tags"] = {}
            event["tags"]["endpoint_type"] = "health_check"
    
    return event


def capture_exception(error: Exception, **kwargs) -> None:
    """
    Manually capture an exception and send to Sentry.
    
    Args:
        error: Exception to capture
        **kwargs: Additional context (user, tags, extra)
    """
    if not settings.SENTRY_DSN:
        return
    
    try:
        sentry_sdk.capture_exception(error, **kwargs)
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")


def capture_message(message: str, level: str = "info", **kwargs) -> None:
    """
    Manually capture a message and send to Sentry.
    
    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **kwargs: Additional context (user, tags, extra)
    """
    if not settings.SENTRY_DSN:
        return
    
    try:
        sentry_sdk.capture_message(message, level=level, **kwargs)
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")


def set_user_context(user_id: str, email: Optional[str] = None, **kwargs) -> None:
    """
    Set user context for Sentry events.
    
    Args:
        user_id: User identifier
        email: User email (will be redacted in before_send)
        **kwargs: Additional user attributes
    """
    if not settings.SENTRY_DSN:
        return
    
    try:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            **kwargs
        })
    except Exception as e:
        logger.error(f"Failed to set user context in Sentry: {e}")


def set_tag(key: str, value: str) -> None:
    """
    Set a tag for Sentry events.
    
    Args:
        key: Tag key
        value: Tag value
    """
    if not settings.SENTRY_DSN:
        return
    
    try:
        sentry_sdk.set_tag(key, value)
    except Exception as e:
        logger.error(f"Failed to set tag in Sentry: {e}")


def set_context(key: str, value: dict) -> None:
    """
    Set additional context for Sentry events.
    
    Args:
        key: Context key
        value: Context dictionary
    """
    if not settings.SENTRY_DSN:
        return
    
    try:
        sentry_sdk.set_context(key, value)
    except Exception as e:
        logger.error(f"Failed to set context in Sentry: {e}")
