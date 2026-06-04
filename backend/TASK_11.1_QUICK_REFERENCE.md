# Task 11.1 Quick Reference: Announcement Creation

## Endpoint

```
POST /api/v1/announcements
```

## Request

```json
{
  "title": "string (1-255 chars, required)",
  "content": "string (min 1 char, required)",
  "target_group": "Team_Members | Ambassadors | All"
}
```

## Response (201 Created)

```json
{
  "id": "uuid",
  "title": "string",
  "content": "string",
  "target_group": "string",
  "created_by_id": "uuid",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Permission Matrix

| Role | Team_Members | Ambassadors | All |
|------|--------------|-------------|-----|
| Overall_Admin | ✅ | ✅ | ✅ |
| Ambassador_Admin | ❌ (403) | ✅ | ✅ |
| Team_Member | ❌ (403) | ❌ (403) | ❌ (403) |
| Ambassador | ❌ (403) | ❌ (403) | ❌ (403) |

## Error Codes

- **401**: Invalid/missing authentication token
- **403**: Insufficient permissions
- **400**: Invalid target_group value
- **422**: Validation error (missing/empty fields)
- **500**: Internal server error

## Examples

### Overall_Admin creates for Team_Members ✅
```bash
curl -X POST http://localhost:8000/api/v1/announcements \
  -H "Authorization: Bearer <overall_admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "content": "All team members please attend",
    "target_group": "Team_Members"
  }'
```

### Ambassador_Admin creates for Ambassadors ✅
```bash
curl -X POST http://localhost:8000/api/v1/announcements \
  -H "Authorization: Bearer <ambassador_admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ambassador Training",
    "content": "Join the training session",
    "target_group": "Ambassadors"
  }'
```

### Ambassador_Admin tries Team_Members ❌
```bash
curl -X POST http://localhost:8000/api/v1/announcements \
  -H "Authorization: Bearer <ambassador_admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Announcement",
    "content": "This will fail",
    "target_group": "Team_Members"
  }'

# Response: 403 Forbidden
# "You do not have permission to create announcements for Team_Members"
```

## Test Commands

```bash
# Run unit tests
pytest tests/test_announcement_endpoints.py -v

# Run property-based tests
pytest tests/test_announcement_properties.py -v

# Run specific property test
pytest tests/test_announcement_properties.py::test_property_28_overall_admin_announcement_targeting -v
pytest tests/test_announcement_properties.py::test_property_29_ambassador_admin_announcement_restriction -v

# Run with coverage
pytest tests/test_announcement_*.py --cov=app.api.announcement --cov-report=term
```

## Key Files

- **Endpoint**: `backend/app/api/announcement.py`
- **Schema**: `backend/app/schemas/announcement.py`
- **RBAC**: `backend/app/core/rbac.py`
- **Model**: `backend/app/models/leaderboard_schedule_announcement.py`
- **Unit Tests**: `backend/tests/test_announcement_endpoints.py`
- **Property Tests**: `backend/tests/test_announcement_properties.py`

## Properties Validated

- ✅ **Property 28**: Overall_Admin can target any group
- ✅ **Property 29**: Ambassador_Admin cannot target Team_Members

## Requirements Validated

- ✅ **Requirement 8.1**: Overall_Admin announcement targeting
- ✅ **Requirement 8.2**: Ambassador_Admin announcement restriction
