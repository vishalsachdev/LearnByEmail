# Scheduler service package
from .apscheduler_service import APSchedulerService
from app.core.error_handler import ServiceErrorHandler

# TODO: Add proper initialization and error handler configuration
scheduler_service_instance = APSchedulerService(error_handler=ServiceErrorHandler())

def get_scheduler_service() -> APSchedulerService:
    """Dependency provider for the scheduler service."""
    # This is a simple singleton for now. 
    # In a real app, you might manage lifetime differently.
    return scheduler_service_instance
