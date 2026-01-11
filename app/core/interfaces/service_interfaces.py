from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union


class EmailServiceInterface(ABC):
    """Interface for email sending services."""
    
    @abstractmethod
    def send_email(self, recipient: str, subject: str, content: str,
                  html_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an email to the specified recipient.
        
        Args:
            recipient: The email address of the recipient
            subject: The email subject line
            content: Plain text content of the email
            html_content: Optional HTML content version of the email
            
        Returns:
            Dict containing status information about the email sending operation
        """
        pass
    
    @abstractmethod
    def send_confirmation_email(self, recipient: str, token: str) -> Dict[str, Any]:
        """
        Send a confirmation email with a verification token.
        
        Args:
            recipient: The email address to confirm
            token: The verification token
            
        Returns:
            Dict containing status information about the email sending operation
        """
        pass
    
    @abstractmethod
    def send_password_reset_email(self, recipient: str, token: str) -> Dict[str, Any]:
        """
        Send a password reset email with a reset token.
        
        Args:
            recipient: The user's email address
            token: The password reset token
            
        Returns:
            Dict containing status information about the email sending operation
        """
        pass
    
    @abstractmethod
    def send_educational_email(self, 
                              recipient: str, 
                              topic: str, 
                              content: str,
                              difficulty: str,
                              lesson_number: int) -> Dict[str, Any]:
        """
        Send an educational email with lesson content.
        
        Args:
            recipient: The student's email address
            topic: The topic of the lesson
            content: The lesson content
            difficulty: The difficulty level of the content
            lesson_number: The sequential lesson number
            
        Returns:
            Dict containing status information about the email sending operation
        """
        pass


class ContentGenerationInterface(ABC):
    """Interface for content generation services."""
    
    @abstractmethod
    def generate_content(self, 
                        topic: str, 
                        difficulty: str,
                        previous_content: Optional[List[Dict[str, Any]]] = None,
                        lesson_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate educational content for a topic.
        
        Args:
            topic: The topic to generate content about
            difficulty: The difficulty level (beginner, intermediate, advanced)
            previous_content: Optional history of previous lessons
            lesson_number: Optional sequential lesson number
            
        Returns:
            Dict containing the generated content and status information
        """
        pass
    
    @abstractmethod
    def generate_preview(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a content preview for a topic.
        
        Args:
            topic: The topic to preview
            difficulty: The difficulty level (beginner, intermediate, advanced)
            
        Returns:
            Dict containing the preview content and status information
        """
        pass


class SchedulerInterface(ABC):
    """Interface for email scheduling services."""
    
    @abstractmethod
    def schedule_email_job(self, subscription_id: int, delivery_time: str, 
                          timezone: str) -> Dict[str, Any]:
        """
        Schedule an email job for a subscription.
        
        Args:
            subscription_id: The ID of the subscription
            delivery_time: The time to deliver the email (format: HH:MM)
            timezone: The user's timezone
            
        Returns:
            Dict containing job information and status
        """
        pass
    
    @abstractmethod
    def remove_jobs_for_subscription(self, subscription_id: int) -> Dict[str, Any]:
        """
        Remove all scheduled jobs for a subscription.
        
        Args:
            subscription_id: The ID of the subscription
            
        Returns:
            Dict containing status information about the operation
        """
        pass
    
    @abstractmethod
    def pause_jobs_for_subscription(self, subscription_id: int, 
                                  resume_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Pause all scheduled jobs for a subscription.
        
        Args:
            subscription_id: The ID of the subscription
            resume_date: Optional date to automatically resume
            
        Returns:
            Dict containing status information about the operation
        """
        pass
    
    @abstractmethod
    def resume_jobs_for_subscription(self, subscription_id: int) -> Dict[str, Any]:
        """
        Resume all scheduled jobs for a subscription.
        
        Args:
            subscription_id: The ID of the subscription
            
        Returns:
            Dict containing status information about the operation
        """
        pass