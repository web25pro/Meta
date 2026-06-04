"""Common schemas for API responses"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail information"""
    field: Optional[str] = Field(None, description="Field name that caused the error (for validation errors)")
    message: str = Field(..., description="Detailed error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    success: bool = Field(False, description="Always false for error responses")
    error: Dict[str, Any] = Field(
        ...,
        description="Error information",
        examples=[
            {
                "code": "INVALID_REQUEST",
                "message": "Invalid request parameters",
                "details": {"field": "email", "message": "Invalid email format"}
            }
        ]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid authentication token",
                        "details": {}
                    }
                },
                {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to perform this action",
                        "details": {"required_role": "Overall_Admin"}
                    }
                },
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request validation failed",
                        "details": {
                            "field": "deadline",
                            "message": "Deadline is required for task creation"
                        }
                    }
                }
            ]
        }


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses"""
    total: int = Field(..., description="Total number of items", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(..., description="Number of items per page", ge=1, le=100)
    total_pages: int = Field(..., description="Total number of pages", ge=0)
    
    @classmethod
    def from_total(cls, total: int, page: int, page_size: int) -> "PaginationMetadata":
        """Create pagination metadata from total count"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


# Common response examples for OpenAPI documentation
COMMON_RESPONSES = {
    401: {
        "description": "Unauthorized - Invalid or missing authentication token",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid authentication token",
                        "details": {}
                    }
                }
            }
        }
    },
    403: {
        "description": "Forbidden - Insufficient permissions",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to perform this action",
                        "details": {"required_role": "Overall_Admin"}
                    }
                }
            }
        }
    },
    404: {
        "description": "Not Found - Resource does not exist",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Resource not found",
                        "details": {}
                    }
                }
            }
        }
    },
    422: {
        "description": "Unprocessable Entity - Validation error",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request validation failed",
                        "details": {
                            "field": "deadline",
                            "message": "Deadline is required"
                        }
                    }
                }
            }
        }
    },
    429: {
        "description": "Too Many Requests - Rate limit exceeded",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "details": {"retry_after": 60}
                    }
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error - Unexpected server error",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {}
                    }
                }
            }
        }
    }
}
