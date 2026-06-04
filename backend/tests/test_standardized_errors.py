"""Tests for standardized error responses (Task 20.2)"""
import pytest
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.exceptions import (
    APIException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    ValidationException,
    RateLimitException,
    InternalServerException,
    ServiceUnavailableException,
)


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_api_exception_base(self):
        """Test base APIException class"""
        exc = APIException(
            message="Test error",
            code="TEST_ERROR",
            status_code=400,
            details={"field": "test"}
        )
        
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"field": "test"}
        
        # Test to_dict method
        result = exc.to_dict()
        assert result == {
            "success": False,
            "error": {
                "code": "TEST_ERROR",
                "message": "Test error",
                "details": {"field": "test"}
            }
        }
    
    def test_bad_request_exception(self):
        """Test BadRequestException (400)"""
        exc = BadRequestException(
            message="Invalid input",
            details={"field": "email"}
        )
        
        assert exc.status_code == 400
        assert exc.code == "BAD_REQUEST"
        assert exc.message == "Invalid input"
        assert exc.details == {"field": "email"}
    
    def test_unauthorized_exception(self):
        """Test UnauthorizedException (401)"""
        exc = UnauthorizedException(
            message="Invalid token"
        )
        
        assert exc.status_code == 401
        assert exc.code == "UNAUTHORIZED"
        assert exc.message == "Invalid token"
    
    def test_forbidden_exception(self):
        """Test ForbiddenException (403)"""
        exc = ForbiddenException(
            details={"required_role": "Overall_Admin"}
        )
        
        assert exc.status_code == 403
        assert exc.code == "FORBIDDEN"
        assert exc.details == {"required_role": "Overall_Admin"}
    
    def test_not_found_exception(self):
        """Test NotFoundException (404)"""
        exc = NotFoundException(
            message="User not found"
        )
        
        assert exc.status_code == 404
        assert exc.code == "NOT_FOUND"
        assert exc.message == "User not found"
    
    def test_conflict_exception(self):
        """Test ConflictException (409)"""
        exc = ConflictException(
            message="Duplicate submission",
            details={"task_id": "123"}
        )
        
        assert exc.status_code == 409
        assert exc.code == "CONFLICT"
        assert exc.message == "Duplicate submission"
    
    def test_validation_exception(self):
        """Test ValidationException (422)"""
        exc = ValidationException(
            details={"field": "deadline", "message": "Required"}
        )
        
        assert exc.status_code == 422
        assert exc.code == "VALIDATION_ERROR"
    
    def test_rate_limit_exception(self):
        """Test RateLimitException (429)"""
        exc = RateLimitException(
            details={"retry_after": 60}
        )
        
        assert exc.status_code == 429
        assert exc.code == "RATE_LIMIT_EXCEEDED"
    
    def test_internal_server_exception(self):
        """Test InternalServerException (500)"""
        exc = InternalServerException()
        
        assert exc.status_code == 500
        assert exc.code == "INTERNAL_SERVER_ERROR"
    
    def test_service_unavailable_exception(self):
        """Test ServiceUnavailableException (503)"""
        exc = ServiceUnavailableException(
            message="Database unavailable"
        )
        
        assert exc.status_code == 503
        assert exc.code == "SERVICE_UNAVAILABLE"


class TestErrorResponseFormat:
    """Test error response format in actual API"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app with exception handlers"""
        from fastapi import FastAPI, Request, status
        from fastapi.responses import JSONResponse
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException
        
        app = FastAPI()
        
        # Add exception handlers
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            errors = []
            for error in exc.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                errors.append({
                    "field": field_path,
                    "message": error["msg"],
                    "type": error["type"]
                })
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request validation failed",
                        "details": {
                            "errors": errors
                        }
                    }
                }
            )
        
        @app.exception_handler(APIException)
        async def api_exception_handler(request: Request, exc: APIException):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict()
            )
        
        @app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            error_codes = {
                400: "BAD_REQUEST",
                401: "UNAUTHORIZED",
                403: "FORBIDDEN",
                404: "NOT_FOUND",
                409: "CONFLICT",
                422: "VALIDATION_ERROR",
                429: "RATE_LIMIT_EXCEEDED",
                500: "INTERNAL_SERVER_ERROR",
                503: "SERVICE_UNAVAILABLE",
            }
            
            error_code = error_codes.get(exc.status_code, "UNKNOWN_ERROR")
            
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": str(exc.detail) if exc.detail else "An error occurred",
                        "details": {}
                    }
                }
            )
        
        # Test endpoints
        @app.get("/test/400")
        async def test_400():
            raise BadRequestException(message="Bad request test")
        
        @app.get("/test/401")
        async def test_401():
            raise UnauthorizedException(message="Unauthorized test")
        
        @app.get("/test/403")
        async def test_403():
            raise ForbiddenException(message="Forbidden test")
        
        @app.get("/test/404")
        async def test_404():
            raise NotFoundException(message="Not found test")
        
        @app.get("/test/409")
        async def test_409():
            raise ConflictException(message="Conflict test")
        
        @app.get("/test/422")
        async def test_422():
            raise ValidationException(message="Validation test")
        
        @app.get("/test/429")
        async def test_429():
            raise RateLimitException(message="Rate limit test")
        
        @app.get("/test/500")
        async def test_500():
            raise InternalServerException(message="Internal error test")
        
        @app.get("/test/503")
        async def test_503():
            raise ServiceUnavailableException(message="Service unavailable test")
        
        class TestModel(BaseModel):
            name: str = Field(..., min_length=1)
            age: int = Field(..., ge=0)
        
        @app.post("/test/validation")
        async def test_validation(data: TestModel):
            return {"message": "success"}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_400_error_format(self, client):
        """Test 400 Bad Request error format"""
        response = client.get("/test/400")
        
        assert response.status_code == 400
        data = response.json()
        
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "BAD_REQUEST"
        assert data["error"]["message"] == "Bad request test"
        assert "details" in data["error"]
    
    def test_401_error_format(self, client):
        """Test 401 Unauthorized error format"""
        response = client.get("/test/401")
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"
        assert data["error"]["message"] == "Unauthorized test"
    
    def test_403_error_format(self, client):
        """Test 403 Forbidden error format"""
        response = client.get("/test/403")
        
        assert response.status_code == 403
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"
        assert data["error"]["message"] == "Forbidden test"
    
    def test_404_error_format(self, client):
        """Test 404 Not Found error format"""
        response = client.get("/test/404")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["message"] == "Not found test"
    
    def test_409_error_format(self, client):
        """Test 409 Conflict error format"""
        response = client.get("/test/409")
        
        assert response.status_code == 409
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "CONFLICT"
        assert data["error"]["message"] == "Conflict test"
    
    def test_422_error_format(self, client):
        """Test 422 Validation Error format"""
        response = client.get("/test/422")
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "Validation test"
    
    def test_422_validation_error_details(self, client):
        """Test 422 validation error with field details"""
        # Missing required fields
        response = client.post("/test/validation", json={})
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "Request validation failed"
        assert "errors" in data["error"]["details"]
        
        errors = data["error"]["details"]["errors"]
        assert len(errors) == 2  # name and age are required
        
        # Check error structure
        for error in errors:
            assert "field" in error
            assert "message" in error
            assert "type" in error
    
    def test_422_validation_error_invalid_type(self, client):
        """Test 422 validation error with invalid type"""
        response = client.post("/test/validation", json={
            "name": "John",
            "age": "not a number"
        })
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "errors" in data["error"]["details"]
    
    def test_422_validation_error_constraint_violation(self, client):
        """Test 422 validation error with constraint violation"""
        response = client.post("/test/validation", json={
            "name": "",  # min_length=1
            "age": -5    # ge=0
        })
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "errors" in data["error"]["details"]
    
    def test_429_error_format(self, client):
        """Test 429 Rate Limit error format"""
        response = client.get("/test/429")
        
        assert response.status_code == 429
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert data["error"]["message"] == "Rate limit test"
    
    def test_500_error_format(self, client):
        """Test 500 Internal Server Error format"""
        response = client.get("/test/500")
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert data["error"]["message"] == "Internal error test"
    
    def test_503_error_format(self, client):
        """Test 503 Service Unavailable error format"""
        response = client.get("/test/503")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert data["error"]["message"] == "Service unavailable test"
    
    def test_error_with_details(self, client):
        """Test error response with additional details"""
        app = client.app
        
        @app.get("/test/error-with-details")
        async def test_error_with_details():
            raise ForbiddenException(
                message="Insufficient permissions",
                details={
                    "required_role": "Overall_Admin",
                    "current_role": "Team_Member"
                }
            )
        
        response = client.get("/test/error-with-details")
        
        assert response.status_code == 403
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"
        assert data["error"]["message"] == "Insufficient permissions"
        assert data["error"]["details"]["required_role"] == "Overall_Admin"
        assert data["error"]["details"]["current_role"] == "Team_Member"


class TestErrorResponseConsistency:
    """Test that all error responses follow the same format"""
    
    def test_all_errors_have_success_false(self):
        """Test that all error responses have success=False"""
        exceptions = [
            BadRequestException(),
            UnauthorizedException(),
            ForbiddenException(),
            NotFoundException(),
            ConflictException(),
            ValidationException(),
            RateLimitException(),
            InternalServerException(),
            ServiceUnavailableException(),
        ]
        
        for exc in exceptions:
            result = exc.to_dict()
            assert result["success"] is False, f"{exc.__class__.__name__} should have success=False"
    
    def test_all_errors_have_required_fields(self):
        """Test that all error responses have required fields"""
        exceptions = [
            BadRequestException(),
            UnauthorizedException(),
            ForbiddenException(),
            NotFoundException(),
            ConflictException(),
            ValidationException(),
            RateLimitException(),
            InternalServerException(),
            ServiceUnavailableException(),
        ]
        
        for exc in exceptions:
            result = exc.to_dict()
            assert "success" in result, f"{exc.__class__.__name__} missing 'success' field"
            assert "error" in result, f"{exc.__class__.__name__} missing 'error' field"
            assert "code" in result["error"], f"{exc.__class__.__name__} missing 'code' field"
            assert "message" in result["error"], f"{exc.__class__.__name__} missing 'message' field"
            assert "details" in result["error"], f"{exc.__class__.__name__} missing 'details' field"
    
    def test_error_codes_are_uppercase(self):
        """Test that all error codes are uppercase"""
        exceptions = [
            BadRequestException(),
            UnauthorizedException(),
            ForbiddenException(),
            NotFoundException(),
            ConflictException(),
            ValidationException(),
            RateLimitException(),
            InternalServerException(),
            ServiceUnavailableException(),
        ]
        
        for exc in exceptions:
            assert exc.code == exc.code.upper(), f"{exc.__class__.__name__} code should be uppercase"
    
    def test_status_codes_match_exception_type(self):
        """Test that status codes match exception types"""
        test_cases = [
            (BadRequestException(), 400),
            (UnauthorizedException(), 401),
            (ForbiddenException(), 403),
            (NotFoundException(), 404),
            (ConflictException(), 409),
            (ValidationException(), 422),
            (RateLimitException(), 429),
            (InternalServerException(), 500),
            (ServiceUnavailableException(), 503),
        ]
        
        for exc, expected_status in test_cases:
            assert exc.status_code == expected_status, \
                f"{exc.__class__.__name__} should have status code {expected_status}"
