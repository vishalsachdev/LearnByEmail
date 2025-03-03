from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import pytz
from fastapi import BackgroundTasks
import logging
import asyncio

from app.core.config import settings
from app.db.models import Subscription

# Create global scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': True,
    'max_instances': 1
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
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


def add_email_job(subscription: Subscription):
    """Add or update an email job in the scheduler"""
    job_id = f'email_{subscription.id}'
    
    # Remove existing job if it exists
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Add new job
    scheduler.add_job(
        func=send_educational_email,
        trigger='cron',
        hour=subscription.preferred_time.hour,
        minute=subscription.preferred_time.minute,
        args=[subscription.id],
        id=job_id,
        replace_existing=True,
        timezone=pytz.timezone(subscription.timezone)
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
    """Initialize jobs for all existing subscriptions"""
    from sqlalchemy.orm import Session
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        subscriptions = db.query(Subscription).all()
        for subscription in subscriptions:
            add_email_job(subscription)
        logger.info(f"Initialized {len(subscriptions)} email jobs")
    finally:
        db.close()