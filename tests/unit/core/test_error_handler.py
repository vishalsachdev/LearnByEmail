import pytest
from app.core.error_handler import ServiceErrorHandler


def test_error_handler_initialization():
    """Test that the error handler initializes correctly."""
    handler = ServiceErrorHandler()
    assert handler is not None
    assert handler.logger is not None


def test_handle_external_service_error():
    """Test the error handling for external services."""
    handler = ServiceErrorHandler()
    
    # Test with a basic exception
    error = ValueError("Test error message")
    result = handler.handle_external_service_error(
        service_name="TestService",
        operation="test_operation",
        error=error
    )
    
    # Check the result structure
    assert result["success"] is False
    assert result["service"] == "TestService"
    assert result["operation"] == "test_operation"
    assert result["error_type"] == "ValueError"
    assert "user_message" in result
    assert "error_code" in result
    

def test_sensitive_info_redaction():
    """Test that sensitive information is properly redacted."""
    handler = ServiceErrorHandler()
    
    # Test with API key in error message
    api_key_error = Exception(
        "Failed to authenticate with API key: sk_test_123456789abcdef"
    )
    result = handler.handle_external_service_error(
        "TestService", "test_operation", api_key_error
    )
    
    # Error message should have redacted the API key
    assert "sk_test_123456789abcdef" not in str(result)
    
    # Test with email address in error message
    email_error = Exception(
        "Failed to send email to user@example.com: connection refused"
    )
    result = handler.handle_external_service_error(
        "TestService", "test_operation", email_error
    )
    
    # Error message should have redacted the email address
    assert "user@example.com" not in str(result)


def test_user_friendly_messages():
    """Test that appropriate user-friendly messages are provided."""
    handler = ServiceErrorHandler()
    
    # Test with common error types
    for error_class, expected_contains in [
        (ConnectionError, "Network connection"),
        (TimeoutError, "timed out"),
        (ValueError, "unexpected error")  # Should use the default message
    ]:
        error = error_class("Test error message")
        result = handler.handle_external_service_error(
            "TestService", "test_operation", error
        )
        
        # Check that the user message contains the expected text
        assert expected_contains.lower() in result["user_message"].lower()


def test_error_code_generation():
    """Test that unique error codes are generated."""
    handler = ServiceErrorHandler()
    
    # Generate multiple error codes
    code1 = handler._get_error_code("TestService", "operation1", "ValueError")
    code2 = handler._get_error_code("TestService", "operation2", "TimeoutError")
    code3 = handler._get_error_code("OtherService", "operation1", "ValueError")
    
    # Codes should be unique
    assert code1 != code2
    assert code1 != code3
    assert code2 != code3
    
    # Codes should follow the expected format
    assert code1.startswith("ERR-TES-OPE-")
    assert code2.startswith("ERR-TES-OPE-")
    assert code3.startswith("ERR-OTH-OPE-")


def test_critical_failure_detection():
    """Test the detection of critical failures based on frequency."""
    handler = ServiceErrorHandler()
    service = "CriticalService"
    operation = "failing_operation"
    error = Exception("Repeated error")
    
    # First failure should not be critical
    result1 = handler.handle_external_service_error(service, operation, error)
    assert result1["critical_error"] is False
    
    # Simulate multiple failures
    for _ in range(4):
        handler._record_service_failure(service, operation)
    
    # After multiple failures, it should be marked critical
    result2 = handler.handle_external_service_error(service, operation, error)
    assert result2["critical_error"] is True