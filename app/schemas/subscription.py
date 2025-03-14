from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, time


class SubscriptionBase(BaseModel):
    email: EmailStr
    topic: str
    preferred_time: time
    timezone: str
    difficulty: Optional[str] = "medium"  # 'easy', 'medium', 'hard'


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    topic: Optional[str] = None
    preferred_time: Optional[time] = None
    timezone: Optional[str] = None
    difficulty: Optional[str] = None  # 'easy', 'medium', 'hard'


class SubscriptionResponse(SubscriptionBase):
    id: int
    created_at: datetime
    last_sent: Optional[datetime] = None
    user_id: int

    class Config:
        from_attributes = True


class EmailHistoryBase(BaseModel):
    content: str
    sent_at: datetime


class EmailHistoryResponse(EmailHistoryBase):
    id: int
    subscription_id: int

    class Config:
        from_attributes = True