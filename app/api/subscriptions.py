from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import User, Subscription, EmailHistory
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
    EmailHistoryResponse
)
from app.services.scheduler import add_email_job, remove_email_job

router = APIRouter()


@router.get("/", response_model=List[SubscriptionResponse])
async def get_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all subscriptions for the current user
    """
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return subscriptions


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_in: SubscriptionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new subscription
    """
    # Check if subscription already exists
    existing = db.query(Subscription).filter(
        Subscription.email == subscription_in.email,
        Subscription.topic == subscription_in.topic,
        Subscription.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a subscription for {subscription_in.topic}",
        )
    
    # Create subscription
    subscription = Subscription(
        **subscription_in.model_dump(),
        user_id=current_user.id
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    # Schedule the email job
    add_email_job(subscription)
    
    # Send an immediate first email
    import asyncio
    import logging
    from app.services.email_sender import send_educational_email_task
    
    logger = logging.getLogger(__name__)
    
    try:
        # Use background_tasks to send the welcome email asynchronously
        background_tasks.add_task(send_educational_email_task, subscription.id)
        logger.info(f"Scheduled immediate welcome email for new API subscription {subscription.id} to {subscription.email}")
    except Exception as e:
        logger.error(f"Error scheduling welcome email for API subscription: {str(e)}")
    
    return subscription


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific subscription by ID
    """
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
        
    return subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    subscription_in: SubscriptionUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a subscription
    """
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Update fields
    update_data = subscription_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)
    
    db.commit()
    db.refresh(subscription)
    
    # Update the email job
    remove_email_job(subscription.id)
    add_email_job(subscription)
    
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a subscription
    """
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Remove the email job first
    remove_email_job(subscription.id)
    
    # Delete the subscription
    db.delete(subscription)
    db.commit()


@router.get("/{subscription_id}/history", response_model=List[EmailHistoryResponse])
async def get_email_history(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
) -> Any:
    """
    Get email history for a subscription
    """
    # First check if subscription exists and belongs to user
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Get email history
    history = (
        db.query(EmailHistory)
        .filter(EmailHistory.subscription_id == subscription_id)
        .order_by(EmailHistory.sent_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return history