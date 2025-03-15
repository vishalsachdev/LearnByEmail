from sqlalchemy import Column, Integer, String, DateTime, Time, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.security import get_password_hash, verify_password
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reset_token = Column(String(256), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    is_admin = Column(Integer, default=0, nullable=False)  # 0=false, 1=true
    
    subscriptions = relationship("Subscription", back_populates="user")
    
    def verify_password(self, password):
        return verify_password(password, self.password_hash)
    
    @staticmethod
    def get_password_hash(password):
        return get_password_hash(password)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), nullable=False)
    topic = Column(String(200), nullable=False)
    preferred_time = Column(Time, nullable=False)
    timezone = Column(String(50), nullable=False)
    difficulty = Column(String(10), default="medium", nullable=False)  # 'easy', 'medium', 'hard'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sent = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="subscriptions")
    email_history = relationship("EmailHistory", back_populates="subscription")
    
    __table_args__ = (
        UniqueConstraint('email', 'topic', 'user_id', name='unique_email_topic_user'),
    )


class EmailHistory(Base):
    __tablename__ = "email_history"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    subscription = relationship("Subscription", back_populates="email_history")