# Task 20.2 Quick Reference: Standardized Error Responses

## Quick Import

```python
from app.core.exceptions import (
    BadRequestException,      # 400
    UnauthorizedException,    # 401
    ForbiddenException,       # 403
    NotFoundException,        # 404
    ConflictException,        # 409
    ValidationException,      # 422
    RateLimitException,       # 429
    InternalServerException,  # 500
    ServiceUnavailableException,  # 503
)
```

## Common Usage Patterns

### 1. Resource Not Found (404)
```python
user = await get_user_by_id(user_id)
if not user:
    raise NotFoundException(message="User not found")
```

### 2. Permission Denied (403)
```python
if current_user.role != "Overall_Admin":
    raise ForbiddenException(
        message="Only Overall_Admin can perform this action",
        details={"required_role": "Overall_Admin"}
    )
```

### 3. Duplicate Resource (409)
```python
existing = await get_submission(task_id, user_id)
if existing:
    raise ConflictException(
        message="Submission already exists for this task",
        details={"task_id": str(task_id)}
    )
```

### 4. Invalid Input (400)
```python
if deadline < datetime.now():
    raise BadRequestException(
        message="Deadline must be in the future",
        details={"deadline": str(deadline)}
    )
```

### 5. Validation Error (422)
```python
# Pydantic handles this automatically, but you can also raise manually:
raise ValidationException(
    message="Invalid task data",
    details={
        "field": "point_value",
        "constraint": "must be greater than 0"
    }
)
```

### 6. Authentication Required (401)
```python
token_data = verify_token(token)
if not token_data:
    raise UnauthorizedException(message="Invalid authentication token")
```

## Error Response Format

All errors return:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

## Status Code → Error Code Mapping

| HTTP Status | Error Code | Exception Class |
|------------|------------|-----------------|
| 400 | BAD_REQUEST | BadRequestException |
| 401 | UNAUTHORIZED | UnauthorizedException |
| 403 | FORBIDDEN | ForbiddenException |
| 404 | NOT_FOUND | NotFoundException |
| 409 | CONFLICT | ConflictException |
| 422 | VALIDATION_ERROR | ValidationException |
| 429 | RATE_LIMIT_EXCEEDED | RateLimitException |
| 500 | INTERNAL_SERVER_ERROR | InternalServerException |
| 503 | SERVICE_UNAVAILABLE | ServiceUnavailableException |

## Validation Error Example

Request:
```json
POST /api/v1/tasks
{
  "title": "",
  "point_value": -10
}
```

Response (422):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "errors": [
        {
          "field": "body -> title",
          "message": "ensure this value has at least 1 characters",
          "type": "value_error.any_str.min_length"
        },
        {
          "field": "body -> point_value",
          "message": "ensure this value is greater than 0",
          "type": "value_error.number.not_gt"
        }
      ]
    }
  }
}
```

## Testing Errors

```python
def test_not_found_error(client):
    response = client.get("/api/v1/users/nonexistent")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
```

## Migration from HTTPException

**Old Code**:
```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="User not found")
```

**New Code**:
```python
from app.core.exceptions import NotFoundException

raise NotFoundException(message="User not found")
```

## Best Practices

1. ✅ Use specific exception classes
2. ✅ Provide clear, actionable messages
3. ✅ Include relevant details (without sensitive data)
4. ✅ Don't log passwords, tokens, or PII
5. ✅ Use appropriate status codes

## Files to Reference

- **Exception Classes**: `backend/app/core/exceptions.py`
- **Exception Handlers**: `backend/app/main.py`
- **Error Middleware**: `backend/app/middleware/error_handler.py`
- **Full Guide**: `backend/ERROR_HANDLING_GUIDE.md`
- **Tests**: `backend/tests/test_error_exceptions.py`
