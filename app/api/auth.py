from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
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
from app.schemas.user import Token, UserCreate, UserResponse, UserPasswordReset, UserResetToken, UserResetPassword, UserConfirmationToken, UserConfirmEmail
from app.services.email_sender import send_password_reset_email, send_confirmation_email
from app.api.base_dependencies import verify_csrf_token
from app.core.rate_limit import strict_rate_limit, standard_rate_limit

router = APIRouter()


@router.post("/login", response_model=Token, dependencies=[Depends(verify_csrf_token), Depends(strict_rate_limit())])
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_csrf_token), Depends(strict_rate_limit())])
async def register_user(
    user_in: UserCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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
    
    # Generate confirmation token
    confirmation_token = generate_reset_token()  # Reuse token generation function
    confirmation_token_expires = get_reset_token_expiry()  # Reuse expiry function
    
    # Create new user with email confirmation fields
    user = User(
        email=user_in.email,
        password_hash=User.get_password_hash(user_in.password),
        email_confirmed=0,  # Not confirmed yet
        confirmation_token=confirmation_token,
        confirmation_token_expires=confirmation_token_expires
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send confirmation email in background
    background_tasks.add_task(
        send_confirmation_email,
        email=str(user.email),
        token=confirmation_token
    )
    
    return user


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user
    """
    return current_user


@router.post("/forgot-password", response_model=UserResetToken, dependencies=[Depends(verify_csrf_token), Depends(strict_rate_limit())])
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


@router.post("/reset-password", response_model=UserResponse, dependencies=[Depends(verify_csrf_token), Depends(strict_rate_limit())])
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


@router.post("/send-confirmation", response_model=UserConfirmationToken, dependencies=[Depends(verify_csrf_token), Depends(strict_rate_limit())])
async def send_confirmation(
    user_data: UserPasswordReset,  # Reuse the email-only schema
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Resend confirmation email for a registered user
    """
    user = db.query(User).filter(User.email == user_data.email).first()
    
    # Always return success even if email not found (to prevent email enumeration)
    if not user:
        # Return a dummy token for non-existent users
        dummy_token = generate_reset_token()
        return {"token": dummy_token}
    
    # Check if already confirmed
    if user.email_confirmed == 1:
        return {"token": "already_confirmed", "status": "success", "message": "Email already confirmed"}
    
    # Generate and store confirmation token for the user
    confirmation_token = generate_reset_token()
    
    # Update user data with SQLAlchemy updates for type safety
    db.query(User).filter(User.id == user.id).update({
        "confirmation_token": confirmation_token,
        "confirmation_token_expires": get_reset_token_expiry()
    })
    db.commit()
    
    # Send confirmation email in background
    background_tasks.add_task(
        send_confirmation_email,
        email=str(user.email),
        token=confirmation_token
    )
    
    return {"token": confirmation_token}


@router.get("/confirm-email", response_model=UserResponse)
async def confirm_email(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Confirm user email using token from URL query parameter
    """
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing confirmation token",
        )
    
    # Find user by confirmation token
    user = db.query(User).filter(
        User.confirmation_token == token,
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation token",
        )
    
    # Check if token is expired
    if not user.confirmation_token_expires or user.confirmation_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation token expired",
        )
    
    # Update user as confirmed and clear token
    db.query(User).filter(User.id == user.id).update({
        "email_confirmed": 1,  # Confirmed
        "confirmation_token": None,
        "confirmation_token_expires": None
    })
    db.commit()
    db.refresh(user)
    
    return user