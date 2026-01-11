import pytest
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import your models
from app.db.base import Base
from app.db.models import User, Subscription, EmailHistory
from app.core.error_handler import ServiceErrorHandler
from app.core.config import settings


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a SQLite in-memory database engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a database session for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def error_handler():
    """Create a service error handler for testing."""
    return ServiceErrorHandler()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$test_hashed_password_hash",
        is_active=True,
        email_confirmed=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_subscription(db_session, test_user):
    """Create a test subscription."""
    subscription = Subscription(
        user_id=test_user.id,
        topic="Python Programming",
        difficulty="intermediate",
        preferred_time="10:00",
        timezone="UTC",
        is_active=True,
        status="active"
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    return subscription


@pytest.fixture
def test_email_history(db_session, test_user, test_subscription):
    """Create test email history entries."""
    histories = []
    now = datetime.utcnow()
    
    # Create 5 email history entries for the past 5 days
    for i in range(5):
        email_date = now - timedelta(days=i)
        history = EmailHistory(
            user_id=test_user.id,
            subscription_id=test_subscription.id,
            content="Test content for day " + str(i),
            sent_at=email_date,
            lesson_number=i + 1,
        )
        db_session.add(history)
        histories.append(history)
    
    db_session.commit()
    
    # Refresh all history objects
    for history in histories:
        db_session.refresh(history)
    
    return histories


@pytest.fixture
def mock_sendgrid():
    """Mock the SendGrid client for testing."""
    class MockSendGridClient:
        def __init__(self, api_key=None):
            self.sent_emails = []
        
        def send(self, message):
            self.sent_emails.append(message)
            # Return a mock response
            return type("MockResponse", (), {"status_code": 202})
    
    return MockSendGridClient()


@pytest.fixture
def mock_gemini():
    """Mock the Gemini content generation API for testing."""
    class MockGeminiResponse:
        def __init__(self, text):
            self.text = text
    
    class MockGeminiClient:
        def __init__(self):
            self.generated_content = {}
        
        def set_response_for_topic(self, topic, difficulty, content):
            key = f"{topic}:{difficulty}"
            self.generated_content[key] = content
        
        def generate_content(self, prompt):
            # Simple mock that returns content based on keywords in the prompt
            for key, content in self.generated_content.items():
                topic, difficulty = key.split(":")
                if topic.lower() in prompt.lower() and difficulty.lower() in prompt.lower():
                    return MockGeminiResponse(content)
            
            # Default response if no matching content
            return MockGeminiResponse("This is mock content generated for testing purposes.")
    
    mock_client = MockGeminiClient()
    
    # Set up some default responses
    mock_client.set_response_for_topic(
        "Python Programming", "beginner", 
        "# Introduction to Python\n\nPython is a versatile programming language..."
    )
    
    mock_client.set_response_for_topic(
        "Python Programming", "intermediate", 
        "# Advanced Python Concepts\n\nLet's explore decorators and context managers..."
    )
    
    mock_client.set_response_for_topic(
        "Data Science", "beginner", 
        "# Introduction to Data Science\n\nData Science combines statistics and programming..."
    )
    
    return mock_client


@pytest.fixture
def test_env_vars():
    """Setup and teardown environment variables for testing."""
    # Save original environment variables
    original_vars = {}
    for key in ["SENDGRID_API_KEY", "GEMINI_API_KEY", "API_SECRET_KEY"]:
        original_vars[key] = os.environ.get(key)
    
    # Set test environment variables
    os.environ["SENDGRID_API_KEY"] = "test_sendgrid_key"
    os.environ["GEMINI_API_KEY"] = "test_gemini_key"
    os.environ["API_SECRET_KEY"] = "test_secret_key_that_is_at_least_32_chars_long"
    
    yield
    
    # Restore original environment variables
    for key, value in original_vars.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value