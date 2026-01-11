import logging
import traceback
import re
from typing import Dict, Any, Optional, List
from datetime import datetime


class ServiceErrorHandler:
    """
    Centralized error handling for service operations.
    
    This class provides standardized error handling, logging, and user-friendly
    messages for service failures.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the error handler with an optional logger.
        
        Args:
            logger: Custom logger instance. If None, a default logger will be created.
        """
        self.logger = logger or logging.getLogger(__name__)
        self._sensitive_patterns = [
            # API keys and secrets typically follow these patterns
            r'(api[_-]?key|apikey|token|secret|password|pwd|auth)[=:"\'\s][^\s&;]{8,}',
            # Email addresses
            r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            # Common API key format in headers
            r'(Bearer|Basic|Token)\s+[A-Za-z0-9._~+/=-]+',
        ]
        
        # Mapping of error types to user-friendly messages
        self._user_messages = {
            # Email service errors
            "SendGridError": "Unable to send email at this time. Please try again later.",
            "SMTPError": "Email delivery is temporarily unavailable. We're working on it.",
            "ConnectionError": "Network connection error. Please check your internet connection.",
            
            # Content generation errors
            "GeminiError": "Content generation is temporarily unavailable. Please try again later.",
            "APIKeyError": "Service configuration error. Please contact support.",
            "TimeoutError": "The operation timed out. Please try again.",
            
            # Scheduler errors
            "SchedulerError": "Unable to schedule the operation. Please try again later.",
            "JobError": "There was a problem with the scheduled task. Please try again.",
            
            # Database errors
            "DatabaseError": "Database operation failed. Please try again later.",
            "IntegrityError": "Data validation error. Please check your input.",
            
            # Default fallback message
            "default": "An unexpected error occurred. Please try again later."
        }
        
        # Keep track of service failures
        self._failure_counts = {}
    
    def handle_external_service_error(self, 
                                     service_name: str, 
                                     operation: str, 
                                     error: Exception, 
                                     user_id: Optional[int] = None,
                                     subscription_id: Optional[int] = None,
                                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle errors from external services with standardized logging and responses.
        
        Args:
            service_name: Name of the service that failed (e.g., "SendGrid", "Gemini")
            operation: The specific operation that failed (e.g., "send_email")
            error: The exception that was raised
            user_id: Optional ID of the affected user
            subscription_id: Optional ID of the affected subscription
            context: Optional additional context data
            
        Returns:
            Dict containing standardized error information
        """
        # Get error details
        error_type = type(error).__name__
        error_message = str(error)
        
        # Redact sensitive information
        redacted_message = self._redact_sensitive_info(error_message)
        
        # Create context dictionary
        log_context = {
            "service": service_name,
            "operation": operation,
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if user_id:
            log_context["user_id"] = user_id
        
        if subscription_id:
            log_context["subscription_id"] = subscription_id
            
        if context:
            log_context.update({k: v for k, v in context.items() if k != "password"})
        
        # Log the error with context
        self.logger.error(
            f"{service_name} error during {operation}: {redacted_message}",
            extra={"context": log_context}
        )
        
        # Log the stack trace at debug level
        self.logger.debug(
            f"Stack trace for {error_type} in {service_name}.{operation}:\n"
            f"{traceback.format_exc()}"
        )
        
        # Record the failure
        self._record_service_failure(service_name, operation)
        
        # Check if this is a critical error
        is_critical = self._is_critical_failure(service_name, operation)
        
        # Generate user-friendly response
        return {
            "success": False,
            "service": service_name,
            "operation": operation,
            "error_type": error_type,
            "user_message": self._get_user_friendly_message(error_type),
            "critical_error": is_critical,
            "error_code": self._get_error_code(service_name, operation, error_type)
        }
    
    def _redact_sensitive_info(self, message: str) -> str:
        """
        Redact sensitive information from error messages.
        
        Args:
            message: The original error message
            
        Returns:
            Redacted message with sensitive information removed
        """
        redacted = message
        for pattern in self._sensitive_patterns:
            redacted = re.sub(pattern, "[REDACTED]", redacted)
        return redacted
    
    def _record_service_failure(self, service_name: str, operation: str) -> None:
        """
        Record a service failure for monitoring and alerting.
        
        Args:
            service_name: Name of the service that failed
            operation: The specific operation that failed
        """
        key = f"{service_name}:{operation}"
        self._failure_counts[key] = self._failure_counts.get(key, 0) + 1
        
        # If too many failures, log a critical message for monitoring
        if self._failure_counts[key] >= 5:
            self.logger.critical(
                f"Service {service_name}.{operation} has failed {self._failure_counts[key]} times"
            )
    
    def _get_user_friendly_message(self, error_type: str) -> str:
        """
        Get a user-friendly error message based on the error type.
        
        Args:
            error_type: The type of exception that occurred
            
        Returns:
            A user-friendly error message
        """
        return self._user_messages.get(error_type, self._user_messages["default"])
    
    def _is_critical_failure(self, service_name: str, operation: str) -> bool:
        """
        Determine if this is a critical service failure.
        
        Args:
            service_name: Name of the service that failed
            operation: The specific operation that failed
            
        Returns:
            True if this is a critical failure, False otherwise
        """
        key = f"{service_name}:{operation}"
        return self._failure_counts.get(key, 0) >= 3
    
    def _get_error_code(self, service_name: str, operation: str, error_type: str) -> str:
        """
        Generate a unique error code for tracking and referencing errors.
        
        Args:
            service_name: Name of the service that failed
            operation: The specific operation that failed
            error_type: The type of exception that occurred
            
        Returns:
            A unique error code
        """
        # Create a unique error code for reference, including service, operation, and error type
        service_code = service_name[:3].upper()
        op_code = operation[:3].upper()
        err_code = error_type[:3].upper()
        timestamp = datetime.utcnow().strftime("%H%M%S")
        return f"ERR-{service_code}-{op_code}-{err_code}-{timestamp}"