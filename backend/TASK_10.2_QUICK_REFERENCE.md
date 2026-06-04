# Task 10.2 Quick Reference: Schedule Update & Delete

## What Was Implemented

### 1. Update Schedule Endpoint
**Endpoint:** `PUT /api/v1/schedules/{schedule_id}`

**Features:**
- Update title, description, event_date, or target_group (all optional)
- Permission checks for admin roles
- Ambassador_Admin cannot set target_group to "Team_Members"
- Returns 404 for deleted schedules

**Example Request:**
```bash
curl -X PUT http://localhost:8000/api/v1/schedules/{id} \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Event Title",
    "description": "New description"
  }'
```

### 2. Delete Schedule Endpoint
**Endpoint:** `DELETE /api/v1/schedules/{schedule_id}`

**Features:**
- Soft delete (sets deleted_at timestamp)
- Preserves all data for audit trail
- Permission checks for admin roles
- Ambassador_Admin cannot delete Team_Members schedules

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/schedules/{id} \
  -H "Authorization: Bearer <token>"
```

## Permission Matrix

| Role | Update | Delete | Restrictions |
|------|--------|--------|--------------|
| Overall_Admin | ✅ | ✅ | None |
| Ambassador_Admin | ✅ | ✅ | Cannot modify Team_Members schedules |
| Team_Member | ❌ | ❌ | No access |
| Ambassador | ❌ | ❌ | No access |

## Files Changed

1. **backend/app/api/schedule.py** - Added 2 new endpoints
2. **backend/tests/test_schedule_endpoints.py** - Added 36 new tests

## Running Tests

```bash
# Using Poetry (recommended)
cd backend
poetry run pytest tests/test_schedule_endpoints.py -v

# Using Docker Compose
docker-compose exec api pytest tests/test_schedule_endpoints.py -v

# Run only update tests
poetry run pytest tests/test_schedule_endpoints.py -k "update" -v

# Run only delete tests
poetry run pytest tests/test_schedule_endpoints.py -k "delete" -v
```

## Validation Rules

### Update Request
- **title**: Optional, 1-255 characters
- **description**: Optional, min 1 character
- **event_date**: Optional, valid ISO datetime
- **target_group**: Optional, one of ["Team_Members", "Ambassadors", "All"]

### Common Errors
- **401**: Invalid/missing token
- **403**: Insufficient permissions
- **404**: Schedule not found or deleted
- **422**: Validation error (empty fields, invalid format)

## Testing Checklist

✅ Overall_Admin can update all fields  
✅ Overall_Admin can delete any schedule  
✅ Ambassador_Admin can update Ambassador/All schedules  
✅ Ambassador_Admin cannot modify Team_Members schedules  
✅ Non-admin users cannot update or delete  
✅ Soft delete preserves data  
✅ Cannot modify deleted schedules  
✅ All validation rules enforced  

## Next Steps

- Task 10.3: Implement schedule retrieval with filtering
- Task 10.4: Implement read-only access enforcement
- Task 10.5: Write property tests for schedule system

## Requirement Validation

✅ **Requirement 7.4**: "THE Platform SHALL allow admins to add and edit schedule events"
- Update endpoint allows editing all schedule fields
- Delete endpoint with soft delete for audit trail
- Permission checks ensure only admins can modify schedules
