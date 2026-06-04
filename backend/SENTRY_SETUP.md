# Sentry Error Tracking and Performance Monitoring Setup

## Overview

This document describes the Sentry integration for error tracking and performance monitoring in the LPanda Platform. The integration provides:

- **Error Tracking**: Automatic capture of all unhandled exceptions
- **Performance Monitoring**: Response time tracking for all API endpoints
- **User Context**: Associate errors with specific users
- **Request Context**: Full request details (endpoint, method, headers, body)
- **Alert Configuration**: Automated alerts for error rate and response time thresholds

## Requirements

**Validates: Requirement 12.2**
- Alert on error rate > 1%
- Alert on response time p95 > 1 second

## Installation

Sentry SDK is already included in `requirements.txt`:

```
sentry-sdk[fastapi]==1.40.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Sentry Error Tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_PROFILES_SAMPLE_RATE=1.0
SENTRY_ENVIRONMENT=production
```

**Configuration Options:**

- `SENTRY_DSN`: Your Sentry project DSN (required to enable Sentry)
- `SENTRY_TRACES_SAMPLE_RATE`: Percentage of transactions to capture (0.0 to 1.0)
  - `1.0` = 100% (recommended for production to meet alert requirements)
  - `0.1` = 10% (for high-traffic applications)
- `SENTRY_PROFILES_SAMPLE_RATE`: Percentage of transactions to profile (0.0 to 1.0)
- `SENTRY_ENVIRONMENT`: Environment name (defaults to `APP_ENV` if not set)

### Getting Your Sentry DSN

1. Sign up for a free account at [sentry.io](https://sentry.io)
2. Create a new project (select "FastAPI" as the platform)
3. Copy the DSN from the project settings
4. Add it to your `.env` file

## Features

### 1. Automatic Error Capture

All unhandled exceptions are automatically captured and sent to Sentry with:

- Full stack trace
- Request context (endpoint, method, headers, query params)
- User context (user_id if authenticated)
- Environment and release information
- Custom tags for categorization

**Example:**

```python
# This error will be automatically captured
@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = await task_service.get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")  # Captured by Sentry
    return task
```

### 2. Manual Error Capture

You can manually capture exceptions or messages:

```python
from app.core.sentry import capture_exception, capture_message

try:
    # Some operation
    result = risky_operation()
except Exception as e:
    # Manually capture with additional context
    capture_exception(
        e,
        tags={"operation": "risky_operation"},
        extra={"input": "some_value"}
    )
    raise

# Capture informational messages
capture_message("Important event occurred", level="info")
```

### 3. User Context

User context is automatically set for authenticated requests:

```python
from app.core.sentry import set_user_context

# Manually set user context
set_user_context(
    user_id="user123",
    email="user@example.com",
    role="Team_Member"
)
```

### 4. Custom Tags and Context

Add custom tags for better filtering in Sentry:

```python
from app.core.sentry import set_tag, set_context

# Add tags
set_tag("feature", "task_submission")
set_tag("user_type", "Ambassador")

# Add structured context
set_context("task", {
    "task_id": "task123",
    "deadline": "2024-01-15",
    "points": 50
})
```

### 5. Performance Monitoring

All API endpoints are automatically instrumented for performance monitoring:

- Response time tracking (p50, p75, p95, p99)
- Database query performance
- Redis operation performance
- Celery task performance

**Viewing Performance Data:**

1. Go to your Sentry project
2. Click "Performance" in the sidebar
3. View transaction summaries and traces

### 6. Data Sanitization

Sensitive data is automatically redacted before sending to Sentry:

**Redacted Headers:**
- `authorization`
- `cookie`
- `x-api-key`
- `x-auth-token`

**Redacted Query Parameters:**
- `password`
- `token`
- `api_key`
- `secret`

**Redacted Body Fields:**
- `password`
- `old_password`
- `new_password`
- `token`
- `refresh_token`
- `access_token`
- `api_key`
- `secret`

**Redacted User Data:**
- `email`
- `username`

## Alert Configuration

### Required Alerts (Requirement 12.2)

Configure the following alerts in your Sentry project dashboard:

#### 1. Error Rate Alert

**Alert when error rate exceeds 1%**

1. Go to **Alerts** → **Create Alert**
2. Select **Issues**
3. Configure:
   - **When**: `The issue is seen`
   - **If**: `more than 1% of sessions`
   - **Then**: Send notification to your team
4. Set alert name: "Error Rate > 1%"
5. Save alert

#### 2. Response Time Alert

**Alert when p95 response time exceeds 1 second**

1. Go to **Alerts** → **Create Alert**
2. Select **Performance**
3. Configure:
   - **When**: `avg(transaction.duration)`
   - **If**: `is above 1000ms` (1 second)
   - **For**: `p95 percentile`
   - **Then**: Send notification to your team
4. Set alert name: "Response Time p95 > 1 second"
5. Save alert

### Additional Recommended Alerts

#### 3. High Error Volume

- **When**: More than 100 errors in 1 hour
- **Action**: Notify on-call engineer

#### 4. New Error Type

- **When**: A new error type is first seen
- **Action**: Notify development team

#### 5. Database Error Spike

- **When**: Database errors increase by 50%
- **Action**: Notify database team

## Error Handler Middleware

The `ErrorHandlerMiddleware` provides:

1. **Categorized Error Handling**:
   - Database errors (SQLAlchemyError) → 503 Service Unavailable
   - Cache errors (RedisError) → 503 Service Unavailable
   - All other errors → 500 Internal Server Error

2. **Standardized Error Responses**:
   ```json
   {
     "success": false,
     "error": {
       "code": "DATABASE_ERROR",
       "message": "A database error occurred. Please try again later.",
       "details": {}
     }
   }
   ```

3. **Automatic Sentry Integration**:
   - All errors are sent to Sentry with appropriate tags
   - User context is automatically included
   - Request context is preserved

## Testing

Run the error tracking tests:

```bash
pytest tests/test_error_tracking.py -v
```

**Test Coverage:**

- Sentry initialization with/without DSN
- Event filtering and sanitization
- Error handler middleware for different error types
- Performance monitoring configuration
- Helper function behavior

## Monitoring Dashboard

### Key Metrics to Monitor

1. **Error Rate**:
   - Target: < 1%
   - Alert threshold: > 1%

2. **Response Time (p95)**:
   - Target: < 500ms
   - Alert threshold: > 1000ms (1 second)

3. **Error Categories**:
   - Database errors
   - Cache errors
   - Unhandled exceptions

4. **Top Errors**:
   - Most frequent errors
   - Errors affecting most users

### Sentry Dashboard Views

1. **Issues**: View all errors grouped by type
2. **Performance**: View transaction performance metrics
3. **Releases**: Track errors by deployment version
4. **Discover**: Custom queries and visualizations

## Troubleshooting

### Sentry Not Capturing Errors

1. **Check DSN Configuration**:
   ```bash
   echo $SENTRY_DSN
   ```

2. **Verify Initialization**:
   - Check application logs for "Sentry initialized successfully"
   - If not present, DSN may be empty or invalid

3. **Test Error Capture**:
   ```python
   from app.core.sentry import capture_message
   capture_message("Test message", level="info")
   ```

### High Error Volume

1. **Check Error Rate Alert**: Should trigger automatically
2. **Review Recent Deployments**: Check if errors started after a deployment
3. **Analyze Error Patterns**: Group by endpoint, user, or error type
4. **Check Database/Redis Health**: May indicate infrastructure issues

### Slow Response Times

1. **Check Performance Alert**: Should trigger if p95 > 1 second
2. **Review Transaction Traces**: Identify slow database queries or external calls
3. **Check Database Performance**: Query execution times, connection pool
4. **Review Redis Performance**: Cache hit rate, connection latency

## Best Practices

1. **Use Appropriate Sample Rates**:
   - Production: 100% (1.0) for accurate alerts
   - High-traffic: 10-50% (0.1-0.5) to reduce costs

2. **Add Context to Errors**:
   ```python
   capture_exception(
       error,
       tags={"feature": "task_submission"},
       extra={"task_id": task_id}
   )
   ```

3. **Monitor Alert Fatigue**:
   - Adjust thresholds if too many false positives
   - Use alert grouping to reduce noise

4. **Regular Review**:
   - Weekly: Review top errors and performance issues
   - Monthly: Analyze trends and adjust alerts
   - Quarterly: Review Sentry configuration and costs

5. **Release Tracking**:
   - Sentry automatically tracks releases using `APP_NAME@API_VERSION`
   - Update `API_VERSION` in `.env` for each deployment

## Security Considerations

1. **PII Protection**:
   - Email and username are automatically redacted
   - Passwords and tokens are never sent to Sentry
   - Custom sanitization in `before_send_filter`

2. **Access Control**:
   - Limit Sentry project access to authorized personnel
   - Use role-based access in Sentry organization

3. **Data Retention**:
   - Configure retention policy in Sentry project settings
   - Default: 90 days for errors, 30 days for performance data

## Cost Optimization

1. **Adjust Sample Rates**:
   - Reduce `SENTRY_TRACES_SAMPLE_RATE` for high-traffic endpoints
   - Use selective sampling for health checks

2. **Filter Noisy Errors**:
   - Configure inbound filters in Sentry project settings
   - Ignore known errors (e.g., bot traffic)

3. **Monitor Quota Usage**:
   - Check Sentry dashboard for quota consumption
   - Set up quota alerts

## References

- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [FastAPI Integration Guide](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Alert Configuration](https://docs.sentry.io/product/alerts/)
