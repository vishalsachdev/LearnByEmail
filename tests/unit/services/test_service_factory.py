import pytest
from unittest.mock import patch, MagicMock

from app.services.service_factory import ServiceFactory
from app.core.interfaces.service_interfaces import (
    EmailServiceInterface,
    ContentGenerationInterface,
    SchedulerInterface
)


def test_get_error_handler():
    """Test that the error handler can be retrieved."""
    handler = ServiceFactory.get_error_handler()
    assert handler is not None
    
    # Getting it again should return the same instance
    handler2 = ServiceFactory.get_error_handler()
    assert handler is handler2


def test_set_testing_mode():
    """Test that setting testing mode works correctly."""
    # Set testing mode
    ServiceFactory.set_testing_mode(True)
    assert ServiceFactory._testing_mode is True
    
    # Reset testing mode for other tests
    ServiceFactory.set_testing_mode(False)
    assert ServiceFactory._testing_mode is False


def test_register_service():
    """Test service registration in testing mode."""
    # Create a mock service
    mock_email_service = MagicMock(spec=EmailServiceInterface)
    
    # Set testing mode
    ServiceFactory.set_testing_mode(True)
    
    # Register the mock service
    ServiceFactory.register_service("email", mock_email_service)
    
    # Retrieve the service
    email_service = ServiceFactory.get_email_service()
    
    # It should be our mock
    assert email_service is mock_email_service
    
    # Reset testing mode for other tests
    ServiceFactory.set_testing_mode(False)


def test_register_service_normal_mode():
    """Test that service registration fails in normal mode."""
    # Create a mock service
    mock_email_service = MagicMock(spec=EmailServiceInterface)
    
    # Make sure testing mode is off
    ServiceFactory.set_testing_mode(False)
    
    # Registering should raise an error in normal mode
    with pytest.raises(RuntimeError):
        ServiceFactory.register_service("email", mock_email_service)


@patch("app.services.service_factory.settings")
def test_email_service_selection_sendgrid(mock_settings):
    """Test email service selection with SendGrid config."""
    # Set up mock settings
    mock_settings.SENDGRID_API_KEY = "test_key"
    mock_settings.SENDGRID_FROM_EMAIL = "test@example.com"
    mock_settings.SENDGRID_FROM_NAME = "Test Sender"
    mock_settings.BASE_URL = "https://example.com"
    
    # Clear existing instances
    ServiceFactory._instances = {}
    
    # Create a mock SendGrid service
    mock_sendgrid_service = MagicMock(spec=EmailServiceInterface)
    
    # Patch the SendGrid service class
    with patch("app.services.email.sendgrid_service.SendGridEmailService", 
               return_value=mock_sendgrid_service):
        
        # Get the email service
        email_service = ServiceFactory.get_email_service()
        
        # It should be our mock
        assert email_service is mock_sendgrid_service


@patch("app.services.service_factory.settings")
def test_email_service_selection_smtp(mock_settings):
    """Test email service selection with SMTP config."""
    # Set up mock settings without SendGrid but with SMTP
    mock_settings.SENDGRID_API_KEY = None
    mock_settings.SMTP_HOST = "smtp.example.com"
    mock_settings.SMTP_PORT = 587
    mock_settings.SMTP_USERNAME = "username"
    mock_settings.SMTP_PASSWORD = "password"
    mock_settings.SMTP_FROM_EMAIL = "test@example.com"
    mock_settings.SMTP_FROM_NAME = "Test Sender"
    mock_settings.SMTP_USE_TLS = True
    mock_settings.BASE_URL = "https://example.com"
    
    # Clear existing instances
    ServiceFactory._instances = {}
    
    # Create a mock SMTP service
    mock_smtp_service = MagicMock(spec=EmailServiceInterface)
    
    # Patch the SMTP service class
    with patch("app.services.email.smtp_service.SMTPEmailService", 
               return_value=mock_smtp_service):
        
        # Get the email service
        email_service = ServiceFactory.get_email_service()
        
        # It should be our mock
        assert email_service is mock_smtp_service


@patch("app.services.service_factory.settings")
def test_email_service_fallback(mock_settings):
    """Test email service fallback to null service."""
    # Set up mock settings with no email config
    mock_settings.SENDGRID_API_KEY = None
    mock_settings.SMTP_HOST = None
    mock_settings.BASE_URL = "https://example.com"
    
    # Clear existing instances
    ServiceFactory._instances = {}
    
    # Create a mock null service
    mock_null_service = MagicMock(spec=EmailServiceInterface)
    
    # Patch the null service class
    with patch("app.services.email.null_service.NullEmailService", 
               return_value=mock_null_service):
        
        # Get the email service
        email_service = ServiceFactory.get_email_service()
        
        # It should be our mock
        assert email_service is mock_null_service


@patch("app.services.service_factory.settings")
def test_content_service_selection(mock_settings):
    """Test content service selection."""
    # Set up mock settings
    mock_settings.GEMINI_API_KEY = "test_key"
    
    # Clear existing instances
    ServiceFactory._instances = {}
    
    # Create a mock Gemini service
    mock_gemini_service = MagicMock(spec=ContentGenerationInterface)
    
    # Patch the Gemini service class
    with patch("app.services.content.gemini_service.GeminiContentService", 
               return_value=mock_gemini_service):
        
        # Get the content service
        content_service = ServiceFactory.get_content_service()
        
        # It should be our mock
        assert content_service is mock_gemini_service


def test_scheduler_service():
    """Test scheduler service creation."""
    # Clear existing instances
    ServiceFactory._instances = {}
    
    # Create a mock scheduler service
    mock_scheduler_service = MagicMock(spec=SchedulerInterface)
    
    # Patch the scheduler service class
    with patch("app.services.scheduler.apscheduler_service.APSchedulerService", 
               return_value=mock_scheduler_service):
        
        # Get the scheduler service
        scheduler_service = ServiceFactory.get_scheduler_service()
        
        # It should be our mock
        assert scheduler_service is mock_scheduler_service