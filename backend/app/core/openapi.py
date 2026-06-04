"""OpenAPI schema customization"""
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation.
    
    This function customizes the auto-generated OpenAPI schema to include:
    - Security scheme definitions
    - Common response schemas
    - Enhanced error documentation
    - Additional metadata
    
    Args:
        app: FastAPI application instance
        
    Returns:
        dict: Customized OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer token authentication. Obtain token via /api/v1/auth/login endpoint."
        }
    }
    
    # Add common response schemas
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
    # Add error response schema
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "success": {
                "type": "boolean",
                "default": False,
                "description": "Always false for error responses"
            },
            "error": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Error code for programmatic handling",
                        "example": "UNAUTHORIZED"
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable error message",
                        "example": "Invalid authentication token"
                    },
                    "details": {
                        "type": "object",
                        "description": "Additional error details",
                        "example": {}
                    }
                },
                "required": ["code", "message"]
            }
        },
        "required": ["success", "error"]
    }
    
    # Add pagination metadata schema
    openapi_schema["components"]["schemas"]["PaginationMetadata"] = {
        "type": "object",
        "properties": {
            "total": {
                "type": "integer",
                "description": "Total number of items",
                "minimum": 0,
                "example": 100
            },
            "page": {
                "type": "integer",
                "description": "Current page number (1-indexed)",
                "minimum": 1,
                "example": 1
            },
            "page_size": {
                "type": "integer",
                "description": "Number of items per page",
                "minimum": 1,
                "maximum": 100,
                "example": 20
            },
            "total_pages": {
                "type": "integer",
                "description": "Total number of pages",
                "minimum": 0,
                "example": 5
            }
        },
        "required": ["total", "page", "page_size", "total_pages"]
    }
    
    # Add common error codes documentation
    openapi_schema["x-error-codes"] = {
        "UNAUTHORIZED": "Invalid or missing authentication token",
        "FORBIDDEN": "Insufficient permissions for this operation",
        "NOT_FOUND": "Requested resource does not exist",
        "VALIDATION_ERROR": "Request validation failed",
        "CONFLICT": "Resource conflict (e.g., duplicate submission)",
        "RATE_LIMIT_EXCEEDED": "Too many requests, rate limit exceeded",
        "INTERNAL_ERROR": "Unexpected server error"
    }
    
    # Add role permissions documentation
    openapi_schema["x-role-permissions"] = {
        "Overall_Admin": {
            "description": "Super administrator with full system access",
            "permissions": [
                "Full access to all users and modules",
                "Create/update/delete tasks for any group",
                "Create/update/delete schedules for any group",
                "Create/update/delete announcements for any group",
                "Manage all user accounts",
                "Access analytics and audit logs"
            ]
        },
        "Ambassador_Admin": {
            "description": "Administrator with restricted access to Ambassador ecosystem",
            "permissions": [
                "Access to Ambassador ecosystem only",
                "Create/update/delete tasks for Ambassadors",
                "Create/update/delete schedules for Ambassadors or All",
                "Create/update/delete announcements for Ambassadors or All",
                "Manage Ambassador accounts only"
            ]
        },
        "Team_Member": {
            "description": "Core team user with task execution capabilities",
            "permissions": [
                "View assigned tasks",
                "Submit tasks",
                "View own points and transaction history",
                "View Team_Member leaderboard",
                "View relevant schedules and announcements"
            ]
        },
        "Ambassador": {
            "description": "Ambassador user with task execution capabilities",
            "permissions": [
                "View assigned tasks",
                "Submit tasks",
                "View own points and transaction history",
                "View Ambassador leaderboard",
                "View relevant schedules and announcements"
            ]
        }
    }
    
    # Add points system documentation
    openapi_schema["x-points-system"] = {
        "description": "Panda Points (PP) reward and penalty system",
        "rewards": {
            "Team_Member_Task_Approval": {
                "amount": 50,
                "description": "Points awarded when a Team_Member's task submission is approved"
            },
            "Ambassador_Task_Approval": {
                "amount": 138.6,
                "description": "Points awarded when an Ambassador's task submission is approved"
            }
        },
        "penalties": {
            "Missed_Deadline": {
                "amount": -100,
                "description": "Points deducted when a task deadline is missed without submission"
            }
        },
        "custom_operations": {
            "Admin_Bonus": "Admins can award custom bonus points to users",
            "Admin_Penalty": "Admins can apply custom penalty points to users"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_openapi(app: FastAPI) -> None:
    """
    Setup custom OpenAPI schema for the application.
    
    Args:
        app: FastAPI application instance
    """
    app.openapi = lambda: custom_openapi(app)
