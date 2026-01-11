import logging
from typing import Dict, Any, Optional, Type, TypeVar, cast

# Import the interfaces
from app.core.interfaces.service_interfaces import (
    EmailServiceInterface,
    ContentGenerationInterface,
    SchedulerInterface
)

# Import the error handler
from app.core.error_handler import ServiceErrorHandler

# Import configuration
from app.core.config import settings

# Type variable for service interfaces
T = TypeVar('T')

class ServiceFactory:
    """
    Factory class for creating and managing service instances.
    
    This class is responsible for:
    1. Creating service instances based on configuration
    2. Providing a centralized access point for services
    3. Managing service lifecycle and dependencies
    4. Facilitating testing by allowing service replacement
    """
    
    # Store singleton instances of services
    _instances: Dict[str, Any] = {}
    
    # Store the error handler instance
    _error_handler: Optional[ServiceErrorHandler] = None
    
    # Track if we're in testing mode
    _testing_mode: bool = False
    
    @classmethod
    def get_error_handler(cls) -> ServiceErrorHandler:
        """
        Get the shared error handler instance.
        
        Returns:
            The error handler instance
        """
        if cls._error_handler is None:
            logger = logging.getLogger("service_errors")
            cls._error_handler = ServiceErrorHandler(logger=logger)
        
        return cls._error_handler
    
    @classmethod
    def set_testing_mode(cls, testing: bool = True) -> None:
        """
        Set the factory to testing mode.
        
        In testing mode, services can be replaced with mocks.
        
        Args:
            testing: Whether to enable testing mode
        """
        cls._testing_mode = testing
        
        # Clear existing instances when changing modes
        if testing:
            cls._instances = {}
    
    @classmethod
    def register_service(cls, service_type: str, instance: Any) -> None:
        """
        Register a service instance for testing.
        
        This method allows tests to replace real services with mocks.
        
        Args:
            service_type: The type of service (e.g., "email", "content")
            instance: The service instance to use
        """
        if not cls._testing_mode:
            raise RuntimeError("register_service can only be called in testing mode")
        
        cls._instances[service_type] = instance
    
    @classmethod
    def get_service(cls, service_type: str, interface_class: Type[T]) -> T:
        """
        Get a service instance of the specified type.
        
        Args:
            service_type: The type of service to get
            interface_class: The interface class to cast the result to
            
        Returns:
            The service instance
        """
        if service_type in cls._instances:
            return cast(interface_class, cls._instances[service_type])
        
        # Service not yet created, create based on type
        if service_type == "email":
            return cast(interface_class, cls._create_email_service())
        elif service_type == "content":
            return cast(interface_class, cls._create_content_service())
        elif service_type == "scheduler":
            return cast(interface_class, cls._create_scheduler_service())
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    
    @classmethod
    def get_email_service(cls) -> EmailServiceInterface:
        """
        Get the email service.
        
        Returns:
            The email service instance
        """
        return cls.get_service("email", EmailServiceInterface)
    
    @classmethod
    def get_content_service(cls) -> ContentGenerationInterface:
        """
        Get the content generation service.
        
        Returns:
            The content generation service instance
        """
        return cls.get_service("content", ContentGenerationInterface)
    
    @classmethod
    def get_scheduler_service(cls) -> SchedulerInterface:
        """
        Get the scheduler service.
        
        Returns:
            The scheduler service instance
        """
        return cls.get_service("scheduler", SchedulerInterface)
    
    @classmethod
    def _create_email_service(cls) -> EmailServiceInterface:
        """
        Create an email service based on available configuration.
        
        Returns:
            An instance of an EmailServiceInterface implementation
        """
        # Import implementations here to avoid circular imports
        # These would be your actual service implementations
        from app.services.email.sendgrid_service import SendGridEmailService
        from app.services.email.smtp_service import SMTPEmailService
        from app.services.email.null_service import NullEmailService
        
        # Get the error handler
        error_handler = cls.get_error_handler()
        
        # Check for SendGrid configuration
        if hasattr(settings, "SENDGRID_API_KEY") and settings.SENDGRID_API_KEY:
            cls._instances["email"] = SendGridEmailService(
                api_key=settings.SENDGRID_API_KEY,
                from_email=settings.SENDGRID_FROM_EMAIL,
                from_name=settings.SENDGRID_FROM_NAME,
                error_handler=error_handler,
                base_url=settings.BASE_URL
            )
            return cls._instances["email"]
        
        # Check for SMTP configuration
        if hasattr(settings, "SMTP_HOST") and settings.SMTP_HOST:
            cls._instances["email"] = SMTPEmailService(
                host=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                from_email=settings.SMTP_FROM_EMAIL,
                from_name=settings.SMTP_FROM_NAME,
                use_tls=settings.SMTP_USE_TLS,
                error_handler=error_handler,
                base_url=settings.BASE_URL
            )
            return cls._instances["email"]
        
        # Fallback to null service
        cls._instances["email"] = NullEmailService(
            error_handler=error_handler,
            base_url=settings.BASE_URL
        )
        return cls._instances["email"]
    
    @classmethod
    def _create_content_service(cls) -> ContentGenerationInterface:
        """
        Create a content generation service based on available configuration.
        
        Returns:
            An instance of a ContentGenerationInterface implementation
        """
        # Import implementations here to avoid circular imports
        from app.services.content.gemini_service import GeminiContentService
        from app.services.content.mock_content_service import MockContentService
        
        # Get the error handler
        error_handler = cls.get_error_handler()
        
        # Check for Gemini API configuration
        if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY:
            cls._instances["content"] = GeminiContentService(
                api_key=settings.GEMINI_API_KEY,
                error_handler=error_handler
            )
            return cls._instances["content"]
        
        # Fallback to mock content service
        cls._instances["content"] = MockContentService(
            error_handler=error_handler
        )
        return cls._instances["content"]
    
    @classmethod
    def _create_scheduler_service(cls) -> SchedulerInterface:
        """
        Create a scheduler service.
        
        Returns:
            An instance of a SchedulerInterface implementation
        """
        # Import implementation here to avoid circular imports
        from app.services.scheduler.apscheduler_service import APSchedulerService
        
        # Get the error handler
        error_handler = cls.get_error_handler()
        
        # Create the scheduler service
        cls._instances["scheduler"] = APSchedulerService(
            error_handler=error_handler
        )
        return cls._instances["scheduler"]