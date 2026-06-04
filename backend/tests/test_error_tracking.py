"""Tests for error tracking and Sentry integration"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from app.core.sentry import (
    init_sentry,
    before_send_filter,
    before_send_transaction_filter,
    capture_exception,
    capture_message,
    set_user_context,
    set_tag,
    set_context,
)
from app.middleware.error_handler import ErrorHandlerMiddleware


class TestSentryIntegration:
    """Test Sentry SDK integration and configuration"""
    
    @patch("app.core.sentry.sentry_sdk.init")
    @patch("app.core.sentry.settings")
    def test_init_sentry_with_dsn(self, mock_settings, mock_sentry_init):
        """Test Sentry initialization with valid DSN"""
        # Arrange
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.APP_ENV = "production"
        mock_settings.SENTRY_ENVIRONMENT = ""
        mock_settings.APP_NAME = "LPanda Platform"
        mock_settings.API_VERSION = "v1"
        mock_settings.SENTRY_TRACES_SAMPLE_RATE = 1.0
        mock_settings.SENTRY_PROFILES_SAMPLE_RATE = 1.0
        
        # Act
        init_sentry()
        
        # Assert
        mock_sentry_init.assert_called_once()
        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["dsn"] == "https://test@sentry.io/123"
        assert call_kwargs["environment"] == "production"
        assert call_kwargs["release"] == "LPanda Platform@v1"
        assert call_kwargs["traces_sample_rate"] == 1.0
        assert call_kwargs["profiles_sample_rate"] == 1.0
        assert call_kwargs["sample_rate"] == 1.0
        assert call_kwargs["send_default_pii"] is False
    
    @patch("app.core.sentry.sentry_sdk.init")
    @patch("app.core.sentry.settings")
    def test_init_sentry_without_dsn(self, mock_settings, mock_sentry_init):
        """Test Sentry initialization skipped when DSN not configured"""
        # Arrange
        mock_settings.SENTRY_DSN = ""
        
        # Act
        init_sentry()
        
        # Assert
        mock_sentry_init.assert_not_called()
    
    @patch("app.core.sentry.sentry_sdk.init")
    @patch("app.core.sentry.settings")
    def test_init_sentry_with_custom_environment(self, mock_settings, mock_sentry_init):
        """Test Sentry initialization with custom environment override"""
        # Arrange
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.APP_ENV = "development"
        mock_settings.SENTRY_ENVIRONMENT = "staging"
        mock_settings.APP_NAME = "LPanda Platform"
        mock_settings.API_VERSION = "v1"
        mock_settings.SENTRY_TRACES_SAMPLE_RATE = 0.5
        mock_settings.SENTRY_PROFILES_SAMPLE_RATE = 0.5
        
        # Act
        init_sentry()
        
        # Assert
        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["environment"] == "staging"


class TestSentryFilters:
    """Test Sentry event filtering and sanitization"""
    
    def test_before_send_filter_sanitizes_headers(self):
        """Test that sensitive headers are redacted"""
        # Arrange
        event = {
            "request": {
                "headers": {
                    "authorization": "Bearer secret-token",
                    "cookie": "session=abc123",
                    "x-api-key": "api-key-123",
                    "content-type": "application/json",
                }
            }
        }
        
        # Act
        filtered_event = before_send_filter(event, {})
        
        # Assert
        assert filtered_event["request"]["headers"]["authorization"] == "***REDACTED***"
        assert filtered_event["request"]["headers"]["cookie"] == "***REDACTED***"
        assert filtered_event["request"]["headers"]["x-api-key"] == "***REDACTED***"
        assert filtered_event["request"]["headers"]["content-type"] == "application/json"
    
    def test_before_send_filter_sanitizes_query_string(self):
        """Test that sensitive query parameters are redacted"""
        # Arrange
        event = {
            "request": {
                "query_string": "api_key=secret123&page=1"
            }
        }
        
        # Act
        filtered_event = before_send_filter(event, {})
        
        # Assert
        assert filtered_event["request"]["query_string"] == "***REDACTED***"
    
    def test_before_send_filter_sanitizes_request_body(self):
        """Test that sensitive body fields are redacted"""
        # Arrange
        event = {
            "request": {
                "data": {
                    "username": "testuser",
                    "password": "secret123",
                    "email": "test@example.com",
                    "token": "jwt-token",
                }
            }
        }
        
        # Act
        filtered_event = before_send_filter(event, {})
        
        # Assert
        assert filtered_event["request"]["data"]["username"] == "testuser"
        assert filtered_event["request"]["data"]["password"] == "***REDACTED***"
        assert filtered_event["request"]["data"]["email"] == "test@example.com"
        assert filtered_event["request"]["data"]["token"] == "***REDACTED***"
    
    def test_before_send_filter_sanitizes_user_data(self):
        """Test that user PII is redacted"""
        # Arrange
        event = {
            "user": {
                "id": "user123",
                "email": "user@example.com",
                "username": "testuser",
            }
        }
        
        # Act
        filtered_event = before_send_filter(event, {})
        
        # Assert
        assert filtered_event["user"]["id"] == "user123"
        assert filtered_event["user"]["email"] == "***REDACTED***"
        assert filtered_event["user"]["username"] == "***REDACTED***"
    
    def test_before_send_transaction_filter_tags_health_checks(self):
        """Test that health check endpoints are tagged"""
        # Arrange
        event = {
            "transaction": "/health"
        }
        
        # Act
        filtered_event = before_send_transaction_filter(event, {})
        
        # Assert
        assert filtered_event["tags"]["endpoint_type"] == "health_check"
    
    def test_before_send_transaction_filter_preserves_other_transactions(self):
        """Test that non-health check transactions are not modified"""
        # Arrange
        event = {
            "transaction": "/api/v1/tasks"
        }
        
        # Act
        filtered_event = before_send_transaction_filter(event, {})
        
        # Assert
        assert "tags" not in filtered_event or "endpoint_type" not in filtered_event.get("tags", {})


class TestSentryHelpers:
    """Test Sentry helper functions"""
    
    @patch("app.core.sentry.sentry_sdk.capture_exception")
    @patch("app.core.sentry.settings")
    def test_capture_exception_with_dsn(self, mock_settings, mock_capture):
        """Test exception capture when Sentry is configured"""
        # Arrange
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        error = ValueError("Test error")
        
        # Act
        capture_exception(error, tags={"custom": "tag"})
        
        # Assert
        mock_capture.assert_called_once_with(error, tags={"custom": "tag"})
    
    @patch("app.core.sentry.sentry_sdk.capture_exception")
    @patch("app.core.sentry.settings")
    def test_capture_exception_without_dsn(self, mock_settings, mock_capture):
        """Test exception capture skipped when Sentry not configured"""
        # Arrange
        mock_settings.SENTRY_DSN = ""
        error = ValueError("Test error")
        
        # Act
        capture_exception(error)
        
        # Assert
        mock_capture.assert_not_called()
    
    @patch("app.core.sentry.sentry_sdk.capture_message")
    @patch("app.core.sentry.settings")
    def test_capture_message_with_dsn(self, mock_settings, mock_capture):
        """Test message capture when Sentry is configured"""
        # Arrange
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        # Act
        capture_message("Test message", level="warning")
        
        # Assert
        mock_capture.assert_called_once_with("Test message", level="warning")
    
    @patch("app.core.sentry.sentry_sdk.set_user")
    @patch("app.core.sentry.settings")
    def test_set_user_context(self, mock_settings, mock_set_user):
        """Test setting user context"""
        # Arrange
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        # Act
        set_user_context(user_id="user123", email="test@example.com")
        
        # Assert
        mock_set_user.assert_called_once_with({
            "id": "user123",
            "email": "test@example.com"
        })
    
    @patch("app.core.sentry.sentry_sdk.set_tag")
    @patch("app.core.sentry.settings")
    def test_set_tag(self, mock_settings, mock_set_tag):
        """Test setting tags"""
        # Arrange
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        # Act
        set_tag("environment", "production")
        
        # Assert
        mock_set_tag.assert_called_once_with("environment", "production")
    
    @patch("app.core.sentry.sentry_sdk.set_context")
    @patch("app.core.sentry.settings")
    def test_set_context(self, mock_settings, mock_set_context):
        """Test setting context"""
        # Arrange
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        
        # Act
        set_context("custom", {"key": "value"})
        
        # Assert
        mock_set_context.assert_called_once_with("custom", {"key": "value"})


class TestErrorHandlerMiddleware:
    """Test error handler middleware"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app with error handler middleware"""
        app = FastAPI()
        app.add_middleware(ErrorHandlerMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        @app.get("/db-error")
        async def db_error_endpoint():
            raise SQLAlchemyError("Database error")
        
        @app.get("/redis-error")
        async def redis_error_endpoint():
            raise RedisError("Redis error")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_successful_request(self, client):
        """Test that successful requests pass through"""
        # Act
        response = client.get("/test")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    @patch("app.middleware.error_handler.capture_exception")
    def test_unhandled_exception(self, mock_capture, client):
        """Test that unhandled exceptions are caught and sent to Sentry"""
        # Act
        response = client.get("/error")
        
        # Assert
        assert response.status_code == 500
        assert response.json()["success"] is False
        assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
        mock_capture.assert_called_once()
    
    @patch("app.middleware.error_handler.capture_exception")
    def test_database_error(self, mock_capture, client):
        """Test that database errors return 503 and are sent to Sentry"""
        # Act
        response = client.get("/db-error")
        
        # Assert
        assert response.status_code == 503
        assert response.json()["success"] is False
        assert response.json()["error"]["code"] == "DATABASE_ERROR"
        mock_capture.assert_called_once()
        
        # Verify error category tag
        call_kwargs = mock_capture.call_args[1]
        assert call_kwargs["tags"]["error_category"] == "database"
    
    @patch("app.middleware.error_handler.capture_exception")
    def test_redis_error(self, mock_capture, client):
        """Test that Redis errors return 503 and are sent to Sentry"""
        # Act
        response = client.get("/redis-error")
        
        # Assert
        assert response.status_code == 503
        assert response.json()["success"] is False
        assert response.json()["error"]["code"] == "CACHE_ERROR"
        mock_capture.assert_called_once()
        
        # Verify error category tag
        call_kwargs = mock_capture.call_args[1]
        assert call_kwargs["tags"]["error_category"] == "cache"


class TestPerformanceMonitoring:
    """Test performance monitoring configuration"""
    
    @patch("app.core.sentry.sentry_sdk.init")
    @patch("app.core.sentry.settings")
    def test_performance_monitoring_enabled(self, mock_settings, mock_sentry_init):
        """Test that performance monitoring is enabled with correct sample rate"""
        # Arrange
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.APP_ENV = "production"
        mock_settings.SENTRY_ENVIRONMENT = ""
        mock_settings.APP_NAME = "LPanda Platform"
        mock_settings.API_VERSION = "v1"
        mock_settings.SENTRY_TRACES_SAMPLE_RATE = 1.0
        mock_settings.SENTRY_PROFILES_SAMPLE_RATE = 1.0
        
        # Act
        init_sentry()
        
        # Assert
        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["traces_sample_rate"] == 1.0
        assert call_kwargs["profiles_sample_rate"] == 1.0
        
        # Verify FastAPI integration is included
        integrations = call_kwargs["integrations"]
        integration_names = [type(i).__name__ for i in integrations]
        assert "FastApiIntegration" in integration_names
        assert "SqlalchemyIntegration" in integration_names
        assert "RedisIntegration" in integration_names
        assert "CeleryIntegration" in integration_names


class TestAlertConfiguration:
    """Test alert configuration (documented in code comments)"""
    
    def test_alert_thresholds_documented(self):
        """Test that alert thresholds are documented in code"""
        # Read sentry.py to verify alert documentation
        with open("app/core/sentry.py", "r") as f:
            content = f.read()
        
        # Assert alert thresholds are documented
        assert "Error rate > 1%" in content
        assert "Response time p95 > 1 second" in content
        assert "Alerts configured in Sentry dashboard" in content
