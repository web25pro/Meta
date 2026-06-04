# Task 10.3 Quick Reference: Schedule Retrieval Endpoints

## Endpoints

### 1. List Schedules (User)
```
GET /api/v1/schedules
```

**Authentication**: Required (Bearer token)

**Query Parameters**:
- `page` (optional): Page number, default=1, min=1
- `page_size` (optional): Items per page, default=20, min=1, max=100

**Behavior**:
- Team_Members see: Team_Members + All schedules
- Ambassadors see: Ambassadors + All schedules
- Filtering based on `user_type`, not `role`
- Excludes deleted schedules
- Ordered by event_date descending

**Response**: `ScheduleListResponse`
```json
{
  "schedules": [...],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

### 2. List All Schedules (Admin)
```
GET /api/v1/schedules/admin
```

**Authentication**: Required (Bearer token)

**Authorization**: Overall_Admin or Ambassador_Admin only

**Query Parameters**:
- `page` (optional): Page number, default=1, min=1
- `page_size` (optional): Items per page, default=20, min=1, max=100

**Behavior**:
- Returns ALL schedules regardless of target_group
- Excludes deleted schedules
- Ordered by event_date descending

**Response**: `ScheduleListResponse`

## Visibility Rules

| User Type | Sees Schedules |
|-----------|----------------|
| Team_Member | Team_Members + All |
| Ambassador | Ambassadors + All |
| Overall_Admin (via /admin) | All schedules |
| Ambassador_Admin (via /admin) | All schedules |

## Key Properties Validated

- **Property 22**: Schedule Segregation - Users only see schedules for their group or "All"
- **Property 26**: Schedule Visibility Filtering - Filtering based on target_group and user_type
- **Property 27**: Non-Admin Read-Only Access - Non-admins can read but not modify

## Test Commands

```bash
# Run all schedule retrieval tests
pytest tests/test_schedule_endpoints.py -k "list_schedules or admin_sees_all" -v

# Run visibility filtering tests
pytest tests/test_schedule_endpoints.py -k "sees_only" -v

# Run admin endpoint tests
pytest tests/test_schedule_endpoints.py -k "admin_endpoint" -v
```

## Example Usage

### User Request
```bash
curl -X GET "http://localhost:8000/api/v1/schedules?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

### Admin Request
```bash
curl -X GET "http://localhost:8000/api/v1/schedules/admin?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

## Error Codes

| Code | Scenario |
|------|----------|
| 200 | Success |
| 401 | Invalid/missing token |
| 403 | Not authenticated (no token) or not admin (for /admin endpoint) |
| 422 | Invalid query parameters (page < 1, page_size < 1 or > 100) |

## Implementation Files

- **API**: `backend/app/api/schedule.py`
- **Tests**: `backend/tests/test_schedule_endpoints.py`
- **Schemas**: `backend/app/schemas/schedule.py`
- **Models**: `backend/app/models/leaderboard_schedule_announcement.py`
