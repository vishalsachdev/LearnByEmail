from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import pytz
from fastapi import BackgroundTasks
import logging
import asyncio

from app.core.config import settings
from app.db.models import Subscription

# Create global scheduler - use simpler setup
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
executors = {
    'default': ThreadPoolExecutor(20)
}
job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': 3600  # Allow misfired jobs up to 1 hour late
}

# Use MemoryJobStore for development to avoid serialization issues
scheduler = AsyncIOScheduler(
    executors=executors,
    job_defaults=job_defaults,
    timezone=pytz.UTC
)

logger = logging.getLogger(__name__)


def start_scheduler():
    """Start the background task scheduler"""
    try:
        scheduler.start()
        logger.info("Scheduler started")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")


async def send_educational_email(subscription_id: int):
    """
    Task to generate and send an educational email
    
    This is the task that APScheduler will call when it's time to send an email
    """
    from app.services.email_sender import send_educational_email_task
    
    # Run the task
    result = await send_educational_email_task(subscription_id)
    
    logger.info(f"Email send task for subscription {subscription_id} completed with result: {result}")


# Create a top-level wrapper function that can be properly serialized
def send_email_wrapper(subscription_id):
    """Wrapper to handle the async function in the scheduler"""
    import asyncio
    import logging
    
    logger = logging.getLogger("app.services.scheduler.wrapper")
    
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Import here to avoid circular imports
        from app.services.email_sender import send_educational_email_task
        
        logger.info(f"Running send_email_wrapper for subscription {subscription_id}")
        result = loop.run_until_complete(send_educational_email_task(subscription_id))
        logger.info(f"Result from email task: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in send_email_wrapper: {type(e).__name__}: {str(e)}")
        return False
    finally:
        loop.close()


def add_email_job(subscription: Subscription):
    """Add or update an email job in the scheduler"""
    job_id = f'email_{subscription.id}'
    
    # Remove existing job if it exists
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Add new job using the top-level wrapper function
    scheduler.add_job(
        func=send_email_wrapper,
        trigger='cron',
        hour=subscription.preferred_time.hour,
        minute=subscription.preferred_time.minute,
        args=[subscription.id],
        id=job_id,
        replace_existing=True,
        timezone=pytz.timezone(str(subscription.timezone))
    )
    
    logger.info(f"Scheduled email job for subscription {subscription.id} at {subscription.preferred_time} {subscription.timezone}")


def remove_email_job(subscription_id: int):
    """Remove an email job from the scheduler"""
    job_id = f'email_{subscription_id}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed email job for subscription {subscription_id}")
    else:
        logger.warning(f"No job found for subscription {subscription_id}")


def init_scheduler_jobs():
    """Initialize jobs for all existing subscriptions from confirmed users"""
    from sqlalchemy.orm import Session
    from app.db.session import SessionLocal
    from app.db.models import User
    
    db = SessionLocal()
    try:
        # Get all subscriptions
        all_subscriptions = db.query(Subscription).all()
        valid_subscriptions = []
        
        for subscription in all_subscriptions:
            # Check confirmation status for all users (since user_id is not nullable)
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if not user:
                logger.error(f"User not found for subscription {subscription.id} with user_id {subscription.user_id}")
                continue
                
            if user.email_confirmed != 1:
                logger.info(f"Skipping job scheduling for subscription {subscription.id} from unconfirmed user {user.id}")
                continue
            
            # Add job for confirmed users
            add_email_job(subscription)
            valid_subscriptions.append(subscription)
        
        logger.info(f"Initialized {len(valid_subscriptions)} email jobs out of {len(all_subscriptions)} total subscriptions")
    finally:
        db.close()