"""Tests for custom exception classes (Task 20.2)"""
import pytest
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    
    def test_default_messages_are_meaningful(self):
        """Test that default error messages are meaningful"""
        exceptions = [
            (BadRequestException(), "Bad request"),
            (UnauthorizedException(), "Authentication required"),
            (ForbiddenException(), "You do not have permission to perform this action"),
            (NotFoundException(), "Resource not found"),
            (ConflictException(), "Request conflicts with current state"),
            (ValidationException(), "Request validation failed"),
            (RateLimitException(), "Rate limit exceeded"),
            (InternalServerException(), "An unexpected error occurred"),
            (ServiceUnavailableException(), "Service temporarily unavailable"),
        ]
        
        for exc, expected_message in exceptions:
            assert exc.message == expected_message, \
                f"{exc.__class__.__name__} should have message '{expected_message}'"
    
    def test_custom_messages_override_defaults(self):
        """Test that custom messages override default messages"""
        exc = BadRequestException(message="Custom error message")
        assert exc.message == "Custom error message"
        
        result = exc.to_dict()
        assert result["error"]["message"] == "Custom error message"
    
    def test_details_default_to_empty_dict(self):
        """Test that details default to empty dict"""
        exc = BadRequestException()
        assert exc.details == {}
        
        result = exc.to_dict()
        assert result["error"]["details"] == {}
    
    def test_custom_details_are_preserved(self):
        """Test that custom details are preserved"""
        details = {
            "field": "email",
            "constraint": "format",
            "value": "invalid-email"
        }
        exc = ValidationException(details=details)
        
        assert exc.details == details
        result = exc.to_dict()
        assert result["error"]["details"] == details


class TestErrorCodeMapping:
    """Test error code mapping for different status codes"""
    
    def test_error_codes_match_http_standards(self):
        """Test that error codes follow HTTP standard naming"""
        test_cases = [
            (400, "BAD_REQUEST"),
            (401, "UNAUTHORIZED"),
            (403, "FORBIDDEN"),
            (404, "NOT_FOUND"),
            (409, "CONFLICT"),
            (422, "VALIDATION_ERROR"),
            (429, "RATE_LIMIT_EXCEEDED"),
            (500, "INTERNAL_SERVER_ERROR"),
            (503, "SERVICE_UNAVAILABLE"),
        ]
        
        exception_map = {
            400: BadRequestException,
            401: UnauthorizedException,
            403: ForbiddenException,
            404: NotFoundException,
            409: ConflictException,
            422: ValidationException,
            429: RateLimitException,
            500: InternalServerException,
            503: ServiceUnavailableException,
        }
        
        for status_code, expected_code in test_cases:
            exc_class = exception_map[status_code]
            exc = exc_class()
            assert exc.code == expected_code, \
                f"Status {status_code} should map to code {expected_code}"
