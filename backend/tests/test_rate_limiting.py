"""Tests for rate limiting middleware"""
import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from redis.asyncio import Redis

from app.middleware.rate_limiting import (
    RateLimitingMiddleware,
    RateLimitConfig,
    extract_user_id_from_request,
    get_rate_limit_key,
    get_endpoint_type,
    get_rate_limit_config,
    check_rate_limit,
)
from app.core.security import create_access_token


@pytest.fixture
def app():
    """Create a test FastAPI app with rate limiting middleware"""
    app = FastAPI()
    app.add_middleware(RateLimitingMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.post("/api/v1/submissions")
    async def test_upload_endpoint():
        return {"message": "uploaded"}
    
    @app.get("/api/v1/leaderboard/team-members")
    async def test_leaderboard_endpoint():
        return {"leaderboard": []}
    
    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """Generate a mock user ID"""
    return "test-user-123"


@pytest.fixture
def auth_token(mock_user_id):
    """Create a valid JWT token"""
    return create_access_token(
        user_id=mock_user_id,
        role="Team_Member",
        user_type="Team_Member"
    )


@pytest.fixture
async def mock_redis():
    """Create a mock Redis client"""
    redis_mock = AsyncMock(spec=Redis)
    
    # Mock pipeline
    pipeline_mock = AsyncMock()
    pipeline_mock.zremrangebyscore = Mock()
    pipeline_mock.zcard = Mock()
    pipeline_mock.execute = AsyncMock(return_value=[None, 0])
    redis_mock.pipeline = Mock(return_value=pipeline_mock)
    
    # Mock other methods
    redis_mock.zadd = AsyncMock()
    redis_mock.expire = AsyncMock()
    redis_mock.zrange = AsyncMock(return_value=[])
    
    return redis_mock


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


class TestGetRateLimitKey:
    """Tests for get_rate_limit_key function"""
    
    def test_key_with_user_id(self):
        """Test key generation with authenticated user"""
        key = get_rate_limit_key("user-123", "192.168.1.1", "general")
        assert key == "rate_limit:general:user-123"
    
    def test_key_without_user_id(self):
        """Test key generation with unauthenticated user (IP-based)"""
        key = get_rate_limit_key(None, "192.168.1.1", "general")
        assert key == "rate_limit:general:ip:192.168.1.1"
    
    def test_key_with_different_endpoint_types(self):
        """Test key generation for different endpoint types"""
        user_id = "user-123"
        client_ip = "192.168.1.1"
        
        general_key = get_rate_limit_key(user_id, client_ip, "general")
        upload_key = get_rate_limit_key(user_id, client_ip, "upload")
        leaderboard_key = get_rate_limit_key(user_id, client_ip, "leaderboard")
        
        assert general_key == "rate_limit:general:user-123"
        assert upload_key == "rate_limit:upload:user-123"
        assert leaderboard_key == "rate_limit:leaderboard:user-123"


class TestGetEndpointType:
    """Tests for get_endpoint_type function"""
    
    def test_upload_endpoint(self):
        """Test detection of file upload endpoint"""
        endpoint_type = get_endpoint_type("/api/v1/submissions", "POST")
        assert endpoint_type == "upload"
    
    def test_leaderboard_endpoint(self):
        """Test detection of leaderboard endpoint"""
        endpoint_type = get_endpoint_type("/api/v1/leaderboard/team-members", "GET")
        assert endpoint_type == "leaderboard"
        
        endpoint_type = get_endpoint_type("/api/v1/leaderboard/ambassadors", "GET")
        assert endpoint_type == "leaderboard"
    
    def test_general_endpoint(self):
        """Test detection of general API endpoint"""
        endpoint_type = get_endpoint_type("/api/v1/tasks", "GET")
        assert endpoint_type == "general"
        
        endpoint_type = get_endpoint_type("/api/v1/users", "POST")
        assert endpoint_type == "general"


class TestGetRateLimitConfig:
    """Tests for get_rate_limit_config function"""
    
    def test_upload_config(self):
        """Test rate limit config for upload endpoints"""
        limit, window = get_rate_limit_config("upload")
        assert limit == RateLimitConfig.FILE_UPLOAD_LIMIT
        assert window == RateLimitConfig.FILE_UPLOAD_WINDOW
        assert limit == 10
        assert window == 60
    
    def test_leaderboard_config(self):
        """Test rate limit config for leaderboard endpoints"""
        limit, window = get_rate_limit_config("leaderboard")
        assert limit == RateLimitConfig.LEADERBOARD_LIMIT
        assert window == RateLimitConfig.LEADERBOARD_WINDOW
        assert limit == 30
        assert window == 60
    
    def test_general_config(self):
        """Test rate limit config for general endpoints"""
        limit, window = get_rate_limit_config("general")
        assert limit == RateLimitConfig.GENERAL_API_LIMIT
        assert window == RateLimitConfig.GENERAL_API_WINDOW
        assert limit == 100
        assert window == 60


class TestCheckRateLimit:
    """Tests for check_rate_limit function"""
    
    @pytest.mark.asyncio
    async def test_allows_request_within_limit(self, mock_redis):
        """Test that requests within limit are allowed"""
        # Mock current count as 5 (below limit of 10)
        mock_redis.pipeline().execute = AsyncMock(return_value=[None, 5])
        
        allowed, remaining, retry_after = await check_rate_limit(
            mock_redis, "test_key", 10, 60
        )
        
        assert allowed is True
        assert remaining == 4  # 10 - 5 - 1
        assert retry_after == 0
        
        # Verify timestamp was added
        mock_redis.zadd.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_denies_request_over_limit(self, mock_redis):
        """Test that requests over limit are denied"""
        # Mock current count as 10 (at limit)
        mock_redis.pipeline().execute = AsyncMock(return_value=[None, 10])
        
        # Mock oldest timestamp
        now = time.time()
        oldest_time = now - 30  # 30 seconds ago
        mock_redis.zrange = AsyncMock(return_value=[("timestamp", oldest_time)])
        
        allowed, remaining, retry_after = await check_rate_limit(
            mock_redis, "test_key", 10, 60
        )
        
        assert allowed is False
        assert remaining == 0
        assert retry_after > 0
        assert retry_after <= 31  # Should be around 30 seconds + 1
        
        # Verify timestamp was NOT added
        mock_redis.zadd.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_removes_old_timestamps(self, mock_redis):
        """Test that old timestamps are removed from window"""
        mock_redis.pipeline().execute = AsyncMock(return_value=[None, 5])
        
        await check_rate_limit(mock_redis, "test_key", 10, 60)
        
        # Verify zremrangebyscore was called to remove old timestamps
        pipeline = mock_redis.pipeline()
        pipeline.zremrangebyscore.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_first_request_allowed(self, mock_redis):
        """Test that first request is always allowed"""
        # Mock current count as 0 (no previous requests)
        mock_redis.pipeline().execute = AsyncMock(return_value=[None, 0])
        
        allowed, remaining, retry_after = await check_rate_limit(
            mock_redis, "test_key", 10, 60
        )
        
        assert allowed is True
        assert remaining == 9  # 10 - 0 - 1
        assert retry_after == 0


class TestRateLimitingMiddleware:
    """Tests for RateLimitingMiddleware"""
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_allows_request_within_limit(self, mock_check, mock_get_redis, client):
        """Test that requests within limit are allowed"""
        # Mock rate limit check to allow request
        mock_check.return_value = (True, 99, 0)
        mock_get_redis.return_value = AsyncMock()
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
        
        # Verify rate limit headers are present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "99"
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_denies_request_over_limit(self, mock_check, mock_get_redis, client):
        """Test that requests over limit are denied with 429"""
        # Mock rate limit check to deny request
        mock_check.return_value = (False, 0, 30)
        mock_get_redis.return_value = AsyncMock()
        
        response = client.get("/test")
        
        assert response.status_code == 429
        
        # Verify error response format
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Rate limit exceeded" in data["error"]["message"]
        assert data["error"]["details"]["retry_after"] == 30
        
        # Verify Retry-After header
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "30"
        assert response.headers["X-RateLimit-Remaining"] == "0"
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_different_limits_for_upload_endpoints(self, mock_check, mock_get_redis, client):
        """Test that upload endpoints have different rate limits"""
        mock_check.return_value = (True, 9, 0)
        mock_get_redis.return_value = AsyncMock()
        
        response = client.post("/api/v1/submissions")
        
        assert response.status_code == 200
        
        # Verify upload limit is used (10 requests/minute)
        assert response.headers["X-RateLimit-Limit"] == "10"
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_different_limits_for_leaderboard_endpoints(self, mock_check, mock_get_redis, client):
        """Test that leaderboard endpoints have different rate limits"""
        mock_check.return_value = (True, 29, 0)
        mock_get_redis.return_value = AsyncMock()
        
        response = client.get("/api/v1/leaderboard/team-members")
        
        assert response.status_code == 200
        
        # Verify leaderboard limit is used (30 requests/minute)
        assert response.headers["X-RateLimit-Limit"] == "30"
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_authenticated_user_rate_limiting(self, mock_check, mock_get_redis, client, auth_token):
        """Test that authenticated users are rate limited by user_id"""
        mock_check.return_value = (True, 99, 0)
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = client.get(
            "/test",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify check_rate_limit was called
        mock_check.assert_called_once()
        
        # Verify key contains user_id (not IP)
        call_args = mock_check.call_args
        key = call_args[0][1]
        assert "test-user-123" in key
        assert "ip:" not in key
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_unauthenticated_user_rate_limiting(self, mock_check, mock_get_redis, client):
        """Test that unauthenticated users are rate limited by IP"""
        mock_check.return_value = (True, 99, 0)
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Verify check_rate_limit was called
        mock_check.assert_called_once()
        
        # Verify key contains IP
        call_args = mock_check.call_args
        key = call_args[0][1]
        assert "ip:" in key
    
    def test_excluded_paths_not_rate_limited(self, client):
        """Test that excluded paths bypass rate limiting"""
        # Health endpoint should not be rate limited
        response = client.get("/health")
        
        assert response.status_code == 200
        
        # Rate limit headers should not be present
        assert "X-RateLimit-Limit" not in response.headers
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_rate_limit_error_allows_request(self, mock_check, mock_get_redis, client):
        """Test that rate limiting errors don't block requests"""
        # Mock Redis error
        mock_get_redis.side_effect = Exception("Redis connection failed")
        
        response = client.get("/test")
        
        # Request should still succeed
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    @patch('app.middleware.rate_limiting.logger')
    async def test_logs_rate_limit_exceeded(self, mock_logger, mock_check, mock_get_redis, client):
        """Test that rate limit exceeded events are logged"""
        mock_check.return_value = (False, 0, 30)
        mock_get_redis.return_value = AsyncMock()
        
        response = client.get("/test")
        
        assert response.status_code == 429
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        log_call = mock_logger.warning.call_args
        assert "Rate limit exceeded" in log_call[0][0]
        assert "endpoint_type" in log_call[1]["extra"]
        assert "retry_after" in log_call[1]["extra"]


class TestRateLimitIntegration:
    """Integration tests for rate limiting"""
    
    @patch('app.middleware.rate_limiting.get_redis')
    async def test_multiple_requests_within_limit(self, mock_get_redis, client):
        """Test multiple requests within rate limit"""
        # Mock Redis to track request count
        request_count = [0]
        
        async def mock_check_rate_limit(redis, key, limit, window):
            request_count[0] += 1
            if request_count[0] <= limit:
                return (True, limit - request_count[0], 0)
            else:
                return (False, 0, 30)
        
        mock_get_redis.return_value = AsyncMock()
        
        with patch('app.middleware.rate_limiting.check_rate_limit', side_effect=mock_check_rate_limit):
            # Make 5 requests (all should succeed)
            for i in range(5):
                response = client.get("/test")
                assert response.status_code == 200
                assert int(response.headers["X-RateLimit-Remaining"]) == 100 - i - 1
    
    @patch('app.middleware.rate_limiting.get_redis')
    async def test_rate_limit_reset_after_window(self, mock_get_redis, client):
        """Test that rate limit resets after time window"""
        mock_get_redis.return_value = AsyncMock()
        
        # First request - allowed
        with patch('app.middleware.rate_limiting.check_rate_limit', return_value=(True, 99, 0)):
            response = client.get("/test")
            assert response.status_code == 200
        
        # Simulate time passing and window reset
        with patch('app.middleware.rate_limiting.check_rate_limit', return_value=(True, 99, 0)):
            response = client.get("/test")
            assert response.status_code == 200


class TestRateLimitHeaders:
    """Tests for rate limit response headers"""
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_rate_limit_headers_on_success(self, mock_check, mock_get_redis, client):
        """Test that rate limit headers are included on successful requests"""
        mock_check.return_value = (True, 50, 0)
        mock_get_redis.return_value = AsyncMock()
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "50"
    
    @patch('app.middleware.rate_limiting.get_redis')
    @patch('app.middleware.rate_limiting.check_rate_limit')
    async def test_rate_limit_headers_on_limit_exceeded(self, mock_check, mock_get_redis, client):
        """Test that rate limit headers are included when limit exceeded"""
        mock_check.return_value = (False, 0, 45)
        mock_get_redis.return_value = AsyncMock()
        
        response = client.get("/test")
        
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        assert response.headers["Retry-After"] == "45"
        assert response.headers["X-RateLimit-Remaining"] == "0"


class TestRateLimitConfiguration:
    """Tests for rate limit configuration values"""
    
    def test_general_api_limit(self):
        """Test general API rate limit configuration"""
        assert RateLimitConfig.GENERAL_API_LIMIT == 100
        assert RateLimitConfig.GENERAL_API_WINDOW == 60
    
    def test_file_upload_limit(self):
        """Test file upload rate limit configuration"""
        assert RateLimitConfig.FILE_UPLOAD_LIMIT == 10
        assert RateLimitConfig.FILE_UPLOAD_WINDOW == 60
    
    def test_leaderboard_limit(self):
        """Test leaderboard rate limit configuration"""
        assert RateLimitConfig.LEADERBOARD_LIMIT == 30
        assert RateLimitConfig.LEADERBOARD_WINDOW == 60
