"""Tests for request/response logging middleware"""
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.request_logging import (
    RequestLoggingMiddleware,
    extract_user_id_from_request,
    sanitize_headers,
    sanitize_query_params,
    SENSITIVE_HEADERS,
    SENSITIVE_QUERY_PARAMS,
)
from app.core.security import create_access_token


@pytest.fixture
def app():
    """Create a test FastAPI app with logging middleware"""
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.post("/test-post")
    async def test_post_endpoint(data: dict):
        return {"received": data}
    
    @app.get("/test-error")
    async def test_error_endpoint():
        raise ValueError("Test error")
    
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """Generate a mock user ID"""
    return str(uuid.uuid4())


@pytest.fixture
def auth_token(mock_user_id):
    """Create a valid JWT token"""
    return create_access_token(
        user_id=mock_user_id,
        role="Team_Member",
        user_type="Team_Member"
    )


class TestExtractUserId:
    """Tests for extract_user_id_from_request function"""
    
    def test_extract_user_id_with_valid_token(self, mock_user_id, auth_token):
        """Test extracting user_id from valid JWT token"""
        request = Mock(spec=Request)
        request.headers = {"authorization": f"Bearer {auth_token}"}
        
        user_id = extract_user_id_from_request(request)
        assert user_id == mock_user_id
    
    def test_extract_user_id_without_auth_header(self):
        """Test extracting user_id when no auth header present"""
        request = Mock(spec=Request)
        request.headers = {}
        
        user_id = extract_user_id_from_request(request)
        assert user_id is None
    
    def test_extract_user_id_with_invalid_token(self):
        """Test extracting user_id with invalid token"""
        request = Mock(spec=Request)
        request.headers = {"authorization": "Bearer invalid-token"}
        
        user_id = extract_user_id_from_request(request)
        assert user_id is None
    
    def test_extract_user_id_with_malformed_header(self):
        """Test extracting user_id with malformed auth header"""
        request = Mock(spec=Request)
        request.headers = {"authorization": "InvalidFormat"}
        
        user_id = extract_user_id_from_request(request)
        assert user_id is None


class TestSanitizeHeaders:
    """Tests for sanitize_headers function"""
    
    def test_sanitize_authorization_header(self):
        """Test that authorization header is redacted"""
        headers = {
            "authorization": "Bearer secret-token",
            "content-type": "application/json"
        }
        
        sanitized = sanitize_headers(headers)
        assert sanitized["authorization"] == "***REDACTED***"
        assert sanitized["content-type"] == "application/json"
    
    def test_sanitize_cookie_header(self):
        """Test that cookie header is redacted"""
        headers = {
            "cookie": "session=abc123",
            "user-agent": "TestClient"
        }
        
        sanitized = sanitize_headers(headers)
        assert sanitized["cookie"] == "***REDACTED***"
        assert sanitized["user-agent"] == "TestClient"
    
    def test_sanitize_multiple_sensitive_headers(self):
        """Test that multiple sensitive headers are redacted"""
        headers = {
            "authorization": "Bearer token",
            "x-api-key": "secret-key",
            "x-auth-token": "auth-token",
            "content-type": "application/json"
        }
        
        sanitized = sanitize_headers(headers)
        assert sanitized["authorization"] == "***REDACTED***"
        assert sanitized["x-api-key"] == "***REDACTED***"
        assert sanitized["x-auth-token"] == "***REDACTED***"
        assert sanitized["content-type"] == "application/json"
    
    def test_sanitize_case_insensitive(self):
        """Test that header sanitization is case-insensitive"""
        headers = {
            "Authorization": "Bearer token",
            "COOKIE": "session=abc",
            "Content-Type": "application/json"
        }
        
        sanitized = sanitize_headers(headers)
        assert sanitized["Authorization"] == "***REDACTED***"
        assert sanitized["COOKIE"] == "***REDACTED***"
        assert sanitized["Content-Type"] == "application/json"


class TestSanitizeQueryParams:
    """Tests for sanitize_query_params function"""
    
    def test_sanitize_password_param(self):
        """Test that password query param is redacted"""
        params = {
            "password": "secret123",
            "username": "testuser"
        }
        
        sanitized = sanitize_query_params(params)
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["username"] == "testuser"
    
    def test_sanitize_token_param(self):
        """Test that token query param is redacted"""
        params = {
            "token": "abc123",
            "page": "1"
        }
        
        sanitized = sanitize_query_params(params)
        assert sanitized["token"] == "***REDACTED***"
        assert sanitized["page"] == "1"
    
    def test_sanitize_multiple_sensitive_params(self):
        """Test that multiple sensitive params are redacted"""
        params = {
            "password": "secret",
            "api_key": "key123",
            "secret": "value",
            "page": "1",
            "limit": "10"
        }
        
        sanitized = sanitize_query_params(params)
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["secret"] == "***REDACTED***"
        assert sanitized["page"] == "1"
        assert sanitized["limit"] == "10"


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware"""
    
    @patch('app.middleware.request_logging.logger')
    def test_logs_successful_request(self, mock_logger, client):
        """Test that successful requests are logged"""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
        
        # Verify request log
        request_call = mock_logger.info.call_args_list[0]
        assert request_call[0][0] == "API Request"
        assert "request_id" in request_call[1]["extra"]
        assert request_call[1]["extra"]["method"] == "GET"
        assert request_call[1]["extra"]["path"] == "/test"
        assert request_call[1]["extra"]["event_type"] == "api_request"
        
        # Verify response log
        response_call = mock_logger.info.call_args_list[1]
        assert response_call[0][0] == "API Response"
        assert response_call[1]["extra"]["status_code"] == 200
        assert "duration_ms" in response_call[1]["extra"]
        assert response_call[1]["extra"]["event_type"] == "api_response"
    
    @patch('app.middleware.request_logging.logger')
    def test_logs_authenticated_request(self, mock_logger, client, auth_token, mock_user_id):
        """Test that authenticated requests include user_id"""
        response = client.get(
            "/test",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify user_id is logged
        request_call = mock_logger.info.call_args_list[0]
        assert request_call[1]["extra"]["user_id"] == mock_user_id
        
        response_call = mock_logger.info.call_args_list[1]
        assert response_call[1]["extra"]["user_id"] == mock_user_id
    
    @patch('app.middleware.request_logging.logger')
    def test_logs_unauthenticated_request(self, mock_logger, client):
        """Test that unauthenticated requests have None user_id"""
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Verify user_id is None
        request_call = mock_logger.info.call_args_list[0]
        assert request_call[1]["extra"]["user_id"] is None
    
    @patch('app.middleware.request_logging.logger')
    def test_logs_request_with_query_params(self, mock_logger, client):
        """Test that query parameters are logged"""
        response = client.get("/test?page=1&limit=10")
        
        assert response.status_code == 200
        
        # Verify query params are logged
        request_call = mock_logger.info.call_args_list[0]
        assert request_call[1]["extra"]["query_params"]["page"] == "1"
        assert request_call[1]["extra"]["query_params"]["limit"] == "10"
    
    @patch('app.middleware.request_logging.logger')
    def test_sanitizes_sensitive_query_params(self, mock_logger, client):
        """Test that sensitive query params are redacted"""
        response = client.get("/test?password=secret&page=1")
        
        assert response.status_code == 200
        
        # Verify sensitive param is redacted
        request_call = mock_logger.info.call_args_list[0]
        assert request_call[1]["extra"]["query_params"]["password"] == "***REDACTED***"
        assert request_call[1]["extra"]["query_params"]["page"] == "1"
    
    @patch('app.middleware.request_logging.logger')
    def test_logs_client_ip_and_user_agent(self, mock_logger, client):
        """Test that client IP and user agent are logged"""
        response = client.get(
            "/test",
            headers={"User-Agent": "TestClient/1.0"}
        )
        
        assert response.status_code == 200
        
        # Verify client info is logged
        request_call = mock_logger.info.call_args_list[0]
        assert "client_ip" in request_call[1]["extra"]
        assert request_call[1]["extra"]["user_agent"] == "TestClient/1.0"
    
    @patch('app.middleware.request_logging.logger')
    def test_logs_error_response(self, mock_logger, client):
        """Test that error responses are logged"""
        with pytest.raises(ValueError):
            client.get("/test-error")
        
        # Verify error log
        error_call = mock_logger.error.call_args_list[0]
        assert error_call[0][0] == "API Request Failed"
        assert error_call[1]["extra"]["status_code"] == 500
        assert "error" in error_call[1]["extra"]
        assert "Test error" in error_call[1]["extra"]["error"]
    
    @patch('app.middleware.request_logging.logger')
    def test_measures_response_time(self, mock_logger, client):
        """Test that response time is measured and logged"""
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Verify duration is logged
        response_call = mock_logger.info.call_args_list[1]
        duration_ms = response_call[1]["extra"]["duration_ms"]
        assert isinstance(duration_ms, (int, float))
        assert duration_ms >= 0
    
    def test_adds_request_id_to_response_headers(self, client):
        """Test that X-Request-ID header is added to response"""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        # Verify it's a valid UUID
        request_id = response.headers["X-Request-ID"]
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail("X-Request-ID is not a valid UUID")
    
    @patch('app.middleware.request_logging.logger')
    def test_logs_post_request(self, mock_logger, client):
        """Test that POST requests are logged"""
        response = client.post("/test-post", json={"key": "value"})
        
        assert response.status_code == 200
        
        # Verify method is logged correctly
        request_call = mock_logger.info.call_args_list[0]
        assert request_call[1]["extra"]["method"] == "POST"
        assert request_call[1]["extra"]["path"] == "/test-post"
    
    @patch('app.middleware.request_logging.logger')
    def test_same_request_id_for_request_and_response(self, mock_logger, client):
        """Test that request and response logs share the same request_id"""
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Get request_id from both logs
        request_call = mock_logger.info.call_args_list[0]
        response_call = mock_logger.info.call_args_list[1]
        
        request_id_1 = request_call[1]["extra"]["request_id"]
        request_id_2 = response_call[1]["extra"]["request_id"]
        
        assert request_id_1 == request_id_2


class TestSensitiveDataExclusion:
    """Tests to verify sensitive data is excluded from logs"""
    
    @patch('app.middleware.request_logging.logger')
    def test_authorization_header_not_logged(self, mock_logger, client, auth_token):
        """Test that authorization header is not logged in plain text"""
        response = client.get(
            "/test",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify token is not in logs
        for call in mock_logger.info.call_args_list:
            log_str = str(call)
            assert auth_token not in log_str
    
    @patch('app.middleware.request_logging.logger')
    def test_password_query_param_not_logged(self, mock_logger, client):
        """Test that password query param is not logged in plain text"""
        response = client.get("/test?password=secret123&page=1")
        
        assert response.status_code == 200
        
        # Verify password is redacted
        request_call = mock_logger.info.call_args_list[0]
        query_params = request_call[1]["extra"]["query_params"]
        assert query_params["password"] == "***REDACTED***"
        assert "secret123" not in str(request_call)


class TestLogRetention:
    """Tests for log rotation and retention configuration"""
    
    @patch('app.core.logging.TimedRotatingFileHandler')
    def test_log_rotation_configured(self, mock_handler):
        """Test that log rotation is configured correctly"""
        from app.core.logging import setup_logging
        from app.core.config import settings
        
        # Set LOG_FILE_PATH to trigger file handler creation
        original_path = getattr(settings, 'LOG_FILE_PATH', '')
        settings.LOG_FILE_PATH = 'logs/test.log'
        
        try:
            setup_logging()
            
            # Verify TimedRotatingFileHandler was called with correct params
            if mock_handler.called:
                call_kwargs = mock_handler.call_args[1]
                assert call_kwargs['when'] == 'midnight'
                assert call_kwargs['interval'] == 1
                assert call_kwargs['backupCount'] == 730  # 2 years
        finally:
            # Restore original setting
            settings.LOG_FILE_PATH = original_path
