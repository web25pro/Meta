"""FastAPI application entry point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.redis import init_redis, close_redis
from app.core.sentry import init_sentry
from app.core.openapi import setup_openapi
from app.core.exceptions import APIException
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.rate_limiting import RateLimitingMiddleware
from app.api import leaderboard, schedule, announcement, community, auth, user, task, submission, points

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize Sentry for error tracking and performance monitoring
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting application", extra={"environment": settings.APP_ENV})
    
    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await close_redis()
    logger.info("Redis connection closed")


# Create FastAPI application with comprehensive OpenAPI documentation
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    description="""
## LPanda Meta-Jungle Task & Reward Management Platform API

A full-stack, role-based task management and gamified reward system that supports 
hierarchical administration and dual user paths (Core Team Members and Ambassadors) 
with a points-based incentive mechanism called Panda Points (PP).

### Key Features

* **Role-Based Access Control**: Four distinct roles (Overall_Admin, Ambassador_Admin, Team_Member, Ambassador)
* **Task Management**: Create, assign, and track tasks with deadlines and point values
* **Submission System**: Submit tasks with text, links, and file uploads
* **Points & Rewards**: Earn Panda Points (PP) for task completion and track transaction history
* **Leaderboard**: Separate leaderboards for Team Members and Ambassadors
* **Schedule Management**: Group-specific calendar events
* **Announcements**: Targeted messaging system for different user groups
* **Deadline Enforcement**: Automatic penalty system for missed deadlines
* **File Upload**: Secure file storage with virus scanning

### Authentication

All endpoints (except `/` and `/health`) require JWT Bearer token authentication.

**To authenticate:**
1. Obtain a JWT token via the `/api/v1/auth/login` endpoint
2. Include the token in the `Authorization` header: `Bearer <token>`
3. Access tokens expire after 15 minutes
4. Use refresh tokens to obtain new access tokens

### Error Codes

The API uses standard HTTP status codes:

* `200` - Success
* `201` - Created
* `204` - No Content (successful deletion)
* `400` - Bad Request (invalid input)
* `401` - Unauthorized (missing or invalid token)
* `403` - Forbidden (insufficient permissions)
* `404` - Not Found
* `409` - Conflict (duplicate submission)
* `422` - Unprocessable Entity (validation error)
* `429` - Too Many Requests (rate limit exceeded)
* `500` - Internal Server Error
* `503` - Service Unavailable

### Rate Limits

* **API Requests**: 100 requests/minute per user
* **File Uploads**: 10 uploads/minute per user
* **Leaderboard Queries**: 30 requests/minute per user

### Pagination

List endpoints support pagination with the following query parameters:
* `page` - Page number (1-indexed, default: 1)
* `page_size` - Items per page (default: 20, max: 100)

Responses include pagination metadata:
* `total` - Total number of items
* `page` - Current page number
* `page_size` - Items per page
    """,
    contact={
        "name": "LPanda Platform Support",
        "email": "support@lpanda.com",
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "authentication",
            "description": "User authentication and session management"
        },
        {
            "name": "users",
            "description": "User management operations (admin only)"
        },
        {
            "name": "tasks",
            "description": "Task creation, assignment, and management"
        },
        {
            "name": "submissions",
            "description": "Task submission and review operations"
        },
        {
            "name": "points",
            "description": "Panda Points (PP) management and transaction history"
        },
        {
            "name": "leaderboard",
            "description": "Leaderboard rankings for Team Members and Ambassadors"
        },
        {
            "name": "schedules",
            "description": "Schedule management for group-specific events"
        },
        {
            "name": "announcements",
            "description": "Announcement system for targeted messaging"
        },
        {
            "name": "files",
            "description": "File upload and storage operations"
        },
        {
            "name": "analytics",
            "description": "System analytics and monitoring (Overall_Admin only)"
        },
        {
            "name": "dashboard",
            "description": "Personalized dashboard data for authenticated users"
        }
    ],
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handler middleware (must be added before request logging)
app.add_middleware(ErrorHandlerMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitingMiddleware)

# Add request/response logging middleware
app.add_middleware(RequestLoggingMiddleware)


# Exception handlers for standardized error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors and return standardized 422 response.
    
    Converts Pydantic validation errors into a user-friendly format with
    field-level error details.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation error
        
    Returns:
        JSONResponse with standardized error format
    """
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Request validation failed",
        extra={
            "endpoint": request.url.path,
            "method": request.method,
            "errors": errors,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": errors
                }
            }
        }
    )


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """
    Handle custom API exceptions and return standardized error response.
    
    Args:
        request: FastAPI request object
        exc: Custom API exception
        
    Returns:
        JSONResponse with standardized error format
    """
    logger.warning(
        f"API exception: {exc.code}",
        extra={
            "error_code": exc.code,
            "message": exc.message,
            "status_code": exc.status_code,
            "endpoint": request.url.path,
            "method": request.method,
            "details": exc.details,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle Starlette HTTP exceptions and return standardized error response.
    
    Args:
        request: FastAPI request object
        exc: Starlette HTTP exception
        
    Returns:
        JSONResponse with standardized error format
    """
    # Map status codes to error codes
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
    
    error_code = error_codes.get(exc.status_code, "UNKNOWN_ERROR")
    
    logger.warning(
        f"HTTP exception: {exc.status_code}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "endpoint": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": str(exc.detail) if exc.detail else "An error occurred",
                "details": {}
            }
        }
    )


# Register routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(task.router)
app.include_router(submission.router)
app.include_router(points.router)
app.include_router(leaderboard.router)
app.include_router(schedule.router)
app.include_router(announcement.router)
app.include_router(community.router)

# Setup custom OpenAPI schema
setup_openapi(app)


@app.get(
    "/",
    tags=["health"],
    summary="Root endpoint",
    description="Returns basic API information including version and environment",
    response_description="API information"
)
async def root():
    """
    Root endpoint providing basic API information.
    
    Returns:
        dict: API name, version, and environment information
    """
    return {
        "message": "LPanda Platform API",
        "version": settings.API_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc"
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Health check endpoint for monitoring and load balancers",
    response_description="Health status",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        },
        503: {
            "description": "Service is unavailable",
            "content": {
                "application/json": {
                    "example": {"status": "unhealthy", "error": "Database connection failed"}
                }
            }
        }
    }
)
async def health_check():
    """
    Health check endpoint for monitoring system status.
    
    This endpoint is used by:
    - Load balancers for health checks
    - Monitoring systems for uptime tracking
    - Kubernetes readiness/liveness probes
    
    Returns:
        dict: Health status information
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
