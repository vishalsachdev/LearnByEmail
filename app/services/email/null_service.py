"""
Null email service implementation.
This service is used as a fallback when no email configuration is available.
"""

from typing import Dict, Any, Optional

from app.core.interfaces.service_interfaces import EmailServiceInterface
from app.core.error_handler import ServiceErrorHandler


class NullEmailService(EmailServiceInterface):
    """
    Null implementation of the email service interface.
    
    This service is used as a fallback when no email configuration is available.
    It logs the email operations but doesn't actually send emails.
    """
    
    def __init__(self, error_handler: ServiceErrorHandler, base_url: str):
        """
        Initialize the null email service.
        
        Args:
            error_handler: Error handler for service errors
            base_url: Base URL for application links
        """
        self.error_handler = error_handler
        self.base_url = base_url
    
    def send_email(self, recipient: str, subject: str, content: str,
                  html_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Log an email without sending it.
        
        Args:
            recipient: The email address of the recipient
            subject: The email subject line
            content: Plain text content of the email
            html_content: Optional HTML content version of the email
            
        Returns:
            Dict containing status information about the operation
        """
        self.error_handler.logger.warning(
            f"NullEmailService: Would send email to {recipient} with subject '{subject}'"
        )
        return {
            "success": False,
            "message": "No email configuration available"
        }
    
    def send_confirmation_email(self, recipient: str, token: str) -> Dict[str, Any]:
        """
        Log a confirmation email without sending it.
        
        Args:
            recipient: The email address to confirm
            token: The verification token
            
        Returns:
            Dict containing status information about the operation
        """
        self.error_handler.logger.warning(
            f"NullEmailService: Would send confirmation email to {recipient}"
        )
        return {
            "success": False,
            "message": "No email configuration available"
        }
    
    def send_password_reset_email(self, recipient: str, token: str) -> Dict[str, Any]:
        """
        Log a password reset email without sending it.
        
        Args:
            recipient: The user's email address
            token: The password reset token
            
        Returns:
            Dict containing status information about the operation
        """
        self.error_handler.logger.warning(
            f"NullEmailService: Would send password reset email to {recipient}"
        )
        return {
            "success": False,
            "message": "No email configuration available"
        }
    
    def send_educational_email(self, 
                              recipient: str, 
                              topic: str, 
                              content: str,
                              difficulty: str,
                              lesson_number: int) -> Dict[str, Any]:
        """
        Log an educational email without sending it.
        
        Args:
            recipient: The student's email address
            topic: The topic of the lesson
            content: The lesson content
            difficulty: The difficulty level of the content
            lesson_number: The sequential lesson number
            
        Returns:
            Dict containing status information about the operation
        """
        self.error_handler.logger.warning(
            f"NullEmailService: Would send educational email to {recipient} "
            f"about '{topic}' (Lesson {lesson_number}, {difficulty})"
        )
        return {
            "success": False,
            "message": "No email configuration available"
        }