from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    generate_reset_token,
    get_reset_token_expiry,
)
from app.db.session import get_db
from app.db.models import User
from app.schemas.user import Token, UserCreate, UserResponse, UserPasswordReset, UserResetToken, UserResetPassword
from app.services.email_sender import send_password_reset_email

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.email, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    # Check if passwords match
    if user_in.password != user_in.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    # Check if user already exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = User(
        email=user_in.email,
        password_hash=User.get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user
    """
    return current_user


@router.post("/forgot-password", response_model=UserResetToken)
async def forgot_password(
    user_data: UserPasswordReset, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request a password reset token
    """
    user = db.query(User).filter(User.email == user_data.email).first()
    
    # Always return success even if email not found (to prevent email enumeration)
    if not user:
        # Return a dummy token for non-existent users
        dummy_token = generate_reset_token()
        return {"token": dummy_token}
    
    # Generate and store reset token for the user
    reset_token = generate_reset_token()
    
    # Update user data with SQLAlchemy updates for type safety
    db.query(User).filter(User.id == user.id).update({
        "reset_token": reset_token,
        "reset_token_expires": get_reset_token_expiry()
    })
    db.commit()
    
    # Send password reset email in background
    background_tasks.add_task(
        send_password_reset_email,
        email=str(user.email),
        token=reset_token
    )
    
    return {"token": reset_token}


@router.post("/reset-password", response_model=UserResponse)
async def reset_password(
    reset_data: UserResetPassword,
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset password using token
    """
    # Check if passwords match
    if reset_data.password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    # Find user by token
    user = db.query(User).filter(
        User.reset_token == reset_data.token,
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )
    
    # Check if token is expired
    if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired",
        )
    
    # Update password and clear token using SQLAlchemy update
    new_password_hash = User.get_password_hash(reset_data.password)
    db.query(User).filter(User.id == user.id).update({
        "password_hash": new_password_hash,
        "reset_token": None,
        "reset_token_expires": None
    })
    db.commit()
    db.refresh(user)
    
    return user