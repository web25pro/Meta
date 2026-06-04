# OpenAPI/Swagger Documentation Implementation

## Overview

This document describes the comprehensive OpenAPI documentation implementation for the LPanda Meta-Jungle Task & Reward Management Platform API.

## Implementation Summary

### 1. FastAPI Application Configuration (app/main.py)

The FastAPI application is configured with comprehensive metadata:

- **Title**: LPanda Meta-Jungle Task & Reward Management Platform
- **Version**: Configured via settings.API_VERSION
- **Description**: Detailed platform overview including:
  - Key features (RBAC, task management, points system, leaderboard, etc.)
  - Authentication requirements (JWT Bearer tokens)
  - Error codes (200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500, 503)
  - Rate limits (API requests, file uploads, leaderboard queries)
  - Pagination parameters and metadata format

- **OpenAPI Tags**: Organized endpoints into logical groups:
  - health: Health check and system status
  - authentication: User authentication and session management
  - users: User management operations
  - tasks: Task creation, assignment, and management
  - submissions: Task submission and review operations
  - points: Panda Points management and transaction history
  - leaderboard: Leaderboard rankings
  - schedules: Schedule management
  - announcements: Announcement system
  - files: File upload and storage
  - analytics: System analytics and monitoring
  - dashboard: Personalized dashboard data

- **Documentation URLs**:
  - OpenAPI JSON: `/api/v1/openapi.json`
  - Swagger UI: `/api/v1/docs`
  - ReDoc: `/api/v1/redoc`

### 2. Custom OpenAPI Schema (app/core/openapi.py)

Enhanced OpenAPI schema with:

#### Security Schemes
- **BearerAuth**: JWT Bearer token authentication
  - Type: HTTP Bearer
  - Format: JWT
  - Description: Obtain token via `/api/v1/auth/login`

#### Common Response Schemas
- **ErrorResponse**: Standardized error format with code, message, and details
- **PaginationMetadata**: Pagination information (total, page, page_size, total_pages)

#### Custom Extensions
- **x-error-codes**: Complete error code reference
  - UNAUTHORIZED: Invalid or missing authentication token
  - FORBIDDEN: Insufficient permissions
  - NOT_FOUND: Resource does not exist
  - VALIDATION_ERROR: Request validation failed
  - CONFLICT: Resource conflict
  - RATE_LIMIT_EXCEEDED: Too many requests
  - INTERNAL_ERROR: Unexpected server error

- **x-role-permissions**: Detailed role permission matrix
  - Overall_Admin: Full system access
  - Ambassador_Admin: Ambassador ecosystem only
  - Team_Member: Task execution and leaderboard access
  - Ambassador: Task execution and leaderboard access

- **x-points-system**: Points reward and penalty documentation
  - Team_Member_Task_Approval: 50 PP
  - Ambassador_Task_Approval: 138.6 PP
  - Missed_Deadline: -100 PP
  - Admin_Bonus: Custom amount
  - Admin_Penalty: Custom amount

### 3. Pydantic Schema Documentation

All Pydantic schemas enhanced with:

#### Authentication Schemas (app/schemas/auth.py)
- **LoginRequest**: Email and password with examples
- **TokenResponse**: Access token, refresh token, expiration details
- **RefreshTokenRequest**: Refresh token for new access token
- **PasswordResetRequest**: Email for password reset
- **PasswordResetConfirm**: Token and new password
- **ChangePasswordRequest**: Current and new password

#### User Schemas (app/schemas/user.py)
- **UserCreate**: User creation with role and type
- **UserUpdate**: Optional fields for user updates
- **UserResponse**: Complete user information with timestamps
- **UserListResponse**: Paginated user list

#### Task Schemas (app/schemas/task.py)
- **TaskCreate**: Task creation with deadline and point value
- **TaskUpdate**: Optional fields for task updates
- **TaskResponse**: Complete task information
- **TaskListResponse**: Paginated task list

#### Submission Schemas (app/schemas/submission.py)
- **SubmissionCreate**: Task submission with content and files
- **SubmissionUpdate**: Update submission content
- **SubmissionFileResponse**: File metadata and scan status
- **SubmissionResponse**: Complete submission information
- **SubmissionListResponse**: Paginated submission list
- **SubmissionReviewRequest**: Approve or reject submission

#### Points Schemas (app/schemas/points.py)
- **PointsTransactionResponse**: Transaction details with type and reason
- **PointsTransactionListResponse**: Paginated transaction history
- **UserPointsResponse**: Current balance and rank
- **AdminBonusRequest**: Award bonus points
- **AdminPenaltyRequest**: Apply penalty points

#### Leaderboard Schemas (app/schemas/leaderboard.py)
- **LeaderboardEntryResponse**: User rank and points
- **LeaderboardResponse**: Paginated leaderboard
- **UserRankResponse**: Individual user rank

#### Schedule Schemas (app/schemas/schedule.py)
- **ScheduleCreateRequest**: Create schedule event
- **ScheduleUpdateRequest**: Update schedule event
- **ScheduleResponse**: Complete schedule information
- **ScheduleListResponse**: Paginated schedule list

#### Announcement Schemas (app/schemas/announcement.py)
- **AnnouncementCreateRequest**: Create announcement
- **AnnouncementUpdateRequest**: Update announcement
- **AnnouncementResponse**: Complete announcement information
- **AnnouncementListResponse**: Paginated announcement list

### 4. API Endpoint Documentation

All API endpoints include:

- **Summary**: Brief endpoint description
- **Description**: Detailed documentation including:
  - Authentication requirements
  - Permission requirements
  - Requirement validation references
  - Business logic explanation
  - Pagination details
  - Caching information (where applicable)

- **Response Examples**: Complete JSON examples for:
  - Success responses (200, 201, 204)
  - Error responses (400, 401, 403, 404, 409, 422, 429, 500)

- **Request Body Examples**: Complete JSON examples for all request schemas

### 5. Common Response Schemas (app/schemas/common.py)

Standardized response formats:

- **ErrorResponse**: Consistent error structure
- **PaginationMetadata**: Pagination helper
- **COMMON_RESPONSES**: Reusable response definitions for:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
  - 422 Validation Error
  - 429 Rate Limit Exceeded
  - 500 Internal Server Error

## Accessing the Documentation

### Swagger UI (Interactive)
Navigate to: `http://localhost:8000/api/v1/docs`

Features:
- Interactive API testing
- Request/response examples
- Authentication testing (JWT tokens)
- Schema exploration
- Try-it-out functionality

### ReDoc (Read-Only)
Navigate to: `http://localhost:8000/api/v1/redoc`

Features:
- Clean, organized documentation
- Search functionality
- Code samples in multiple languages
- Downloadable OpenAPI spec

### OpenAPI JSON
Download the raw OpenAPI specification: `http://localhost:8000/api/v1/openapi.json`

Use with:
- Postman (import collection)
- API testing tools
- Code generators
- Documentation generators

## Key Features

### 1. Authentication Documentation
- Clear JWT token flow explanation
- Token expiration times (15 minutes for access, 7 days for refresh)
- Bearer token format examples
- Security scheme definitions

### 2. Error Code Documentation
- Complete error code reference
- HTTP status code mapping
- Error response format examples
- Field-level validation error details

### 3. Role-Based Access Control
- Permission matrix for all roles
- Endpoint-level permission requirements
- Scope enforcement documentation

### 4. Points System Documentation
- Reward amounts for each user type
- Penalty amounts and conditions
- Transaction type explanations
- Idempotency guarantees

### 5. Pagination Documentation
- Query parameter descriptions
- Response metadata format
- Default and maximum page sizes
- Total count calculation

### 6. Rate Limiting Documentation
- Rate limits per endpoint category
- Retry-after headers
- Rate limit error responses

## Validation

The OpenAPI documentation validates:

✅ **Requirements 1.1**: Authentication and RBAC documentation
✅ **Requirements 2.1**: Task management endpoint documentation
✅ All request/response schemas documented
✅ Authentication requirements specified
✅ Error codes and responses documented
✅ Pagination parameters documented
✅ Rate limits documented
✅ Role permissions documented
✅ Points system documented

## Testing the Documentation

### Manual Testing
1. Start the application: `make dev` or `poetry run uvicorn app.main:app --reload`
2. Navigate to `http://localhost:8000/api/v1/docs`
3. Verify all endpoints are documented
4. Test authentication flow with JWT tokens
5. Verify request/response examples are accurate

### Automated Testing
Run the OpenAPI generation test:
```bash
poetry run python test_openapi_generation.py
```

This verifies:
- OpenAPI schema generation
- Security schemes configuration
- Common schemas presence
- Custom extensions
- API metadata

## Maintenance

### Adding New Endpoints
1. Add endpoint to appropriate router file
2. Include `summary` and `description` parameters
3. Specify `response_model` for success responses
4. Add `responses` dict for error responses
5. Document authentication requirements
6. Reference requirement numbers

### Adding New Schemas
1. Create Pydantic model in appropriate schema file
2. Add field descriptions using `Field(..., description="...")`
3. Add examples using `Field(..., examples=[...])`
4. Add `model_config` with `json_schema_extra` for complete examples
5. Set `from_attributes=True` for ORM models

### Updating Documentation
1. Update schema descriptions and examples
2. Update endpoint descriptions
3. Update error response examples
4. Update custom extensions in `openapi.py`
5. Test documentation in Swagger UI

## Best Practices

1. **Consistent Descriptions**: Use clear, concise language
2. **Complete Examples**: Provide realistic, complete JSON examples
3. **Error Documentation**: Document all possible error responses
4. **Authentication**: Always specify authentication requirements
5. **Permissions**: Document required roles/permissions
6. **Validation**: Document validation rules and constraints
7. **Business Logic**: Explain important business rules
8. **References**: Link to requirement numbers for traceability

## Conclusion

The OpenAPI documentation provides comprehensive, interactive API documentation that:
- Helps developers understand and use the API
- Enables automated testing and code generation
- Documents authentication and authorization
- Explains error handling and validation
- Provides complete request/response examples
- Supports multiple documentation formats (Swagger UI, ReDoc, JSON)

All endpoints, schemas, and error responses are fully documented according to OpenAPI 3.0 specification.
