# Task 11.2 Implementation Summary: Announcement Update and Deletion

## Overview
Successfully implemented PUT and DELETE endpoints for announcements with proper permission checks, scope enforcement, and soft delete functionality.

## Implementation Details

### 1. API Endpoints Added

#### PUT /api/v1/announcements/:id
- **Purpose**: Update existing announcements
- **Request Body**: AnnouncementUpdateRequest (all fields optional)
  - `title`: Optional string (1-255 characters)
  - `content`: Optional string (min 1 character)
  - `target_group`: Optional string (Team_Members, Ambassadors, or All)
- **Response**: AnnouncementResponse (200 OK)
- **Status Codes**:
  - 200: Successfully updated
  - 400: Invalid target_group value
  - 401: Invalid or missing authentication token
  - 403: Permission denied
  - 404: Announcement not found or already deleted
  - 500: Internal server error

#### DELETE /api/v1/announcements/:id
- **Purpose**: Soft delete announcements
- **Request Body**: None
- **Response**: None (204 No Content)
- **Status Codes**:
  - 204: Successfully deleted
  - 401: Invalid or missing authentication token
  - 403: Permission denied
  - 404: Announcement not found or already deleted
  - 500: Internal server error

### 2. Permission Enforcement

Both endpoints enforce the following RBAC rules:

**Overall_Admin**:
- Can update/delete any announcement
- Can change target_group to any value (Team_Members, Ambassadors, All)

**Ambassador_Admin**:
- Can update/delete announcements for Ambassadors or All
- Cannot update announcement to Team_Members target_group
- Cannot delete announcements with Team_Members target_group

**Team_Member and Ambassador**:
- Cannot update or delete any announcements
- Receive 403 Forbidden error

### 3. Key Features

#### Update Endpoint
- **Optional Fields**: All fields in update request are optional
- **Partial Updates**: Only provided fields are updated
- **Scope Enforcement**: Ambassador_Admin cannot update to Team_Members target_group
- **Timestamp Management**: 
  - `created_at` is maintained (not modified)
  - `updated_at` is set to current UTC time
- **Validation**: Same validation as create endpoint for target_group

#### Delete Endpoint
- **Soft Delete**: Sets `deleted_at` timestamp instead of removing record
- **Audit Trail**: Maintains record for audit purposes
- **Scope Enforcement**: Ambassador_Admin cannot delete Team_Members announcements
- **Idempotency**: Attempting to delete already-deleted announcement returns 404

### 4. Files Modified

#### backend/app/api/announcement.py
- Added `update_announcement()` function (lines 180-313)
- Added `delete_announcement()` function (lines 315-405)
- Both functions follow the same pattern as schedule.py endpoints

#### backend/app/core/rbac.py
- Permissions already existed:
  - `Permission.UPDATE_ANNOUNCEMENT`
  - `Permission.DELETE_ANNOUNCEMENT`
- Both permissions assigned to OVERALL_ADMIN and AMBASSADOR_ADMIN roles

#### backend/tests/test_announcement_endpoints.py
- Added 23 new test cases covering:
  - Update functionality (title, content, target_group, all fields)
  - Delete functionality (soft delete verification)
  - Permission enforcement for both endpoints
  - Scope enforcement (Ambassador_Admin restrictions)
  - Error cases (404, 403, 400)
  - Timestamp management (created_at maintenance)

### 5. Test Coverage

**Update Tests** (13 tests):
- ✅ Overall_Admin can update title
- ✅ Overall_Admin can update content
- ✅ Overall_Admin can update target_group
- ✅ Overall_Admin can update all fields at once
- ✅ Ambassador_Admin can update announcements for Ambassadors
- ✅ Ambassador_Admin cannot update to Team_Members target_group
- ✅ Team_Member cannot update announcements
- ✅ Update non-existent announcement returns 404
- ✅ Update with invalid target_group returns 400/422
- ✅ created_at timestamp is maintained after update

**Delete Tests** (10 tests):
- ✅ Overall_Admin can delete any announcement
- ✅ Ambassador_Admin can delete announcements for Ambassadors
- ✅ Ambassador_Admin cannot delete Team_Members announcements
- ✅ Team_Member cannot delete announcements
- ✅ Delete non-existent announcement returns 404
- ✅ Delete already-deleted announcement returns 404
- ✅ Soft delete sets deleted_at timestamp

### 6. Requirement Validation

**Validates Requirement 8.5**:
- ✅ Update endpoint: title, content, target_group (optional fields)
- ✅ Delete endpoint: soft delete (set deleted_at timestamp)
- ✅ Permission checks: admin only
- ✅ Scope enforcement: Ambassador_Admin cannot update to Team_Members
- ✅ Maintain created_at for chronological ordering

### 7. Design Pattern Consistency

The implementation follows the exact pattern from `backend/app/api/schedule.py`:
- Same permission checking logic
- Same scope enforcement using `can_create_announcement_for_group()`
- Same soft delete implementation
- Same error handling and logging
- Same response structure

### 8. Security Considerations

- **Authentication**: Both endpoints require valid JWT token
- **Authorization**: RBAC enforced via `has_permission()` check
- **Scope Enforcement**: Ambassador_Admin restrictions properly enforced
- **Soft Delete**: Maintains audit trail by setting deleted_at instead of hard delete
- **Input Validation**: Pydantic schemas validate all input data
- **SQL Injection**: Protected by SQLAlchemy ORM
- **Logging**: All operations logged with user ID and role for audit

### 9. Database Impact

**No schema changes required**:
- `deleted_at` column already exists in announcements table
- `updated_at` column already exists and is automatically updated
- `created_at` column is maintained (not modified on update)

### 10. API Documentation

Both endpoints are automatically documented via FastAPI:
- OpenAPI/Swagger UI available at `/docs`
- ReDoc available at `/redoc`
- Includes request/response schemas, status codes, and descriptions

## Testing Instructions

To run the tests:

```bash
# Run all announcement tests
poetry run pytest tests/test_announcement_endpoints.py -v

# Run only update tests
poetry run pytest tests/test_announcement_endpoints.py -k "update" -v

# Run only delete tests
poetry run pytest tests/test_announcement_endpoints.py -k "delete" -v

# Run with coverage
poetry run pytest tests/test_announcement_endpoints.py --cov=app.api.announcement --cov-report=term
```

## Example Usage

### Update Announcement Title
```bash
curl -X PUT "http://localhost:8000/api/v1/announcements/{id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

### Update All Fields
```bash
curl -X PUT "http://localhost:8000/api/v1/announcements/{id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Title",
    "content": "New content",
    "target_group": "All"
  }'
```

### Delete Announcement
```bash
curl -X DELETE "http://localhost:8000/api/v1/announcements/{id}" \
  -H "Authorization: Bearer {token}"
```

## Completion Status

✅ **Task 11.2 Complete**

All requirements have been implemented:
- ✅ PUT /api/v1/announcements/:id endpoint
- ✅ DELETE /api/v1/announcements/:id endpoint
- ✅ Update: title, content, target_group (optional fields)
- ✅ Delete: soft delete (set deleted_at timestamp)
- ✅ Permission checks: admin only
- ✅ Scope enforcement: Ambassador_Admin restrictions
- ✅ Maintain created_at for chronological ordering
- ✅ Comprehensive test coverage (23 new tests)
- ✅ Follows schedule.py pattern exactly
- ✅ Proper logging and error handling
