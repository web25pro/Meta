# Error Handling Guide - Task 20.2 Implementation

## Overview

This document describes the standardized error response format implemented for the LPanda Task & Reward Platform API. All API endpoints return errors in a consistent format with appropriate HTTP status codes.

## Error Response Format

All error responses follow this standardized format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additional": "context-specific information"
    }
  }
}
```

### Fields

- **success** (boolean): Always `false` for error responses
- **error** (object): Error information container
  - **code** (string): Machine-readable error code in UPPERCASE_SNAKE_CASE
  - **message** (string): Human-readable error description
  - **details** (object): Additional context-specific error information

## HTTP Status Codes

The API uses the following HTTP status codes:

### 400 Bad Request
**Code**: `BAD_REQUEST`

Used when the request is malformed or contains invalid data.

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid request parameters",
    "details": {
      "field": "date_format",
      "expected": "YYYY-MM-DD"
    }
  }
}
```

### 401 Unauthorized
**Code**: `UNAUTHORIZED`

Used when authentication is required but missing or invalid.

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid authentication token",
    "details": {}
  }
}
```

### 403 Forbidden
**Code**: `FORBIDDEN`

Used when the user is authenticated but lacks permission for the requested action.

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to perform this action",
    "details": {
      "required_role": "Overall_Admin",
      "current_role": "Team_Member"
    }
  }
}
```

### 404 Not Found
**Code**: `NOT_FOUND`

Used when a requested resource does not exist.

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "User not found",
    "details": {
      "user_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  }
}
```

### 409 Conflict
**Code**: `CONFLICT`

Used when the request conflicts with the current state (e.g., duplicate submission).

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "Duplicate submission detected",
    "details": {
      "task_id": "123e4567-e89b-12d3-a456-426614174000",
      "existing_submission_id": "987e6543-e21b-12d3-a456-426614174000"
    }
  }
}
```

### 422 Unprocessable Entity
**Code**: `VALIDATION_ERROR`

Used when request validation fails. Includes detailed field-level error information.

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "errors": [
        {
          "field": "body -> deadline",
          "message": "field required",
          "type": "missing"
        },
        {
          "field": "body -> point_value",
          "message": "ensure this value is greater than 0",
          "type": "value_error"
        }
      ]
    }
  }
}
```

### 429 Too Many Requests
**Code**: `RATE_LIMIT_EXCEEDED`

Used when rate limit is exceeded.

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Maximum 100 requests per 60 seconds allowed.",
    "details": {
      "limit": 100,
      "window": 60,
      "retry_after": 45
    }
  }
}
```

**Response Headers**:
- `Retry-After`: Seconds until rate limit resets
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### 500 Internal Server Error
**Code**: `INTERNAL_SERVER_ERROR`

Used when an unexpected error occurs on the server.

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later.",
    "details": {}
  }
}
```

### 503 Service Unavailable
**Code**: `SERVICE_UNAVAILABLE`

Used when a required service (database, cache, etc.) is unavailable.

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Database temporarily unavailable. Please try again later.",
    "details": {}
  }
}
```

## Using Custom Exceptions in Code

### Import Exceptions

```python
from app.core.exceptions import (
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    ValidationException,
    RateLimitException,
    InternalServerException,
    ServiceUnavailableException,
)
```

### Raise Exceptions

```python
# Simple usage with default message
raise NotFoundException()

# Custom message
raise NotFoundException(message="Task not found")

# With additional details
raise ForbiddenException(
    message="Insufficient permissions",
    details={
        "required_role": "Overall_Admin",
        "current_role": "Team_Member"
    }
)

# Validation error with field details
raise ValidationException(
    message="Invalid task data",
    details={
        "field": "deadline",
        "constraint": "must be in the future",
        "value": "2024-01-01"
    }
)
```

### Exception Hierarchy

All custom exceptions inherit from `APIException`:

```python
class APIException(Exception):
    def __init__(self, message, code, status_code, details=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self):
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }
```

## Exception Handlers

The application includes global exception handlers that automatically convert exceptions to standardized error responses:

### 1. Custom API Exceptions
Handles all exceptions inheriting from `APIException`.

### 2. Request Validation Errors
Handles Pydantic validation errors and converts them to 422 responses with detailed field-level errors.

### 3. HTTP Exceptions
Handles FastAPI/Starlette HTTP exceptions and converts them to standardized format.

### 4. Database Errors
Handles SQLAlchemy errors and returns 503 Service Unavailable.

### 5. Cache Errors
Handles Redis errors and returns 503 Service Unavailable.

### 6. Unhandled Exceptions
Catches all other exceptions and returns 500 Internal Server Error.

## Error Logging

All errors are logged with appropriate context:

```python
logger.warning(
    "API exception: FORBIDDEN",
    extra={
        "error_code": "FORBIDDEN",
        "message": "Insufficient permissions",
        "status_code": 403,
        "endpoint": "/api/v1/tasks",
        "method": "POST",
        "details": {"required_role": "Overall_Admin"}
    }
)
```

Server errors (5xx) are also sent to Sentry for monitoring.

## Best Practices

### 1. Use Specific Exceptions
Choose the most specific exception for the error condition:

```python
# Good
raise NotFoundException(message="User not found")

# Avoid
raise HTTPException(status_code=404, detail="User not found")
```

### 2. Provide Meaningful Messages
Error messages should be clear and actionable:

```python
# Good
raise ValidationException(
    message="Task deadline must be in the future",
    details={"field": "deadline", "value": "2024-01-01"}
)

# Avoid
raise ValidationException(message="Invalid input")
```

### 3. Include Relevant Details
Add context that helps debugging without exposing sensitive information:

```python
# Good
raise ConflictException(
    message="Duplicate submission detected",
    details={"task_id": str(task_id)}
)

# Avoid exposing internal details
raise ConflictException(
    message="Duplicate submission",
    details={"sql_error": "UNIQUE constraint failed"}
)
```

### 4. Don't Log Sensitive Data
Never include passwords, tokens, or PII in error details:

```python
# Good
raise UnauthorizedException(message="Invalid credentials")

# NEVER do this
raise UnauthorizedException(
    message="Invalid credentials",
    details={"password": user_password}
)
```

## Testing Error Responses

### Unit Tests

```python
def test_not_found_exception():
    exc = NotFoundException(message="User not found")
    
    assert exc.status_code == 404
    assert exc.code == "NOT_FOUND"
    assert exc.message == "User not found"
    
    result = exc.to_dict()
    assert result["success"] is False
    assert result["error"]["code"] == "NOT_FOUND"
```

### Integration Tests

```python
def test_api_returns_404_for_missing_user(client):
    response = client.get("/api/v1/users/nonexistent-id")
    
    assert response.status_code == 404
    data = response.json()
    
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()
```

## Migration Guide

### Updating Existing Endpoints

Replace `HTTPException` with custom exceptions:

**Before**:
```python
from fastapi import HTTPException

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**After**:
```python
from app.core.exceptions import NotFoundException

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise NotFoundException(message="User not found")
    return user
```

## Summary

The standardized error response format provides:

1. **Consistency**: All errors follow the same structure
2. **Machine-readable codes**: Error codes enable programmatic error handling
3. **Human-readable messages**: Clear descriptions for developers and users
4. **Detailed context**: Additional information for debugging
5. **Proper HTTP status codes**: Semantic status codes for different error types
6. **Validation details**: Field-level error information for 422 responses

This implementation satisfies **Requirement 1.1** for standardized error handling across the API.
