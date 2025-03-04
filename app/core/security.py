from datetime import datetime, timedelta
from typing import Any, Union, Optional
import secrets
import logging
import uuid

from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.user import TokenPayload

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Get password hash"""
    return pwd_context.hash(password)


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Any:
    """Get current user from token"""
    from app.db.models import User
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = db.query(User).filter(User.email == token_data.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


# Create a new security scheme that doesn't require authentication and checks cookies
class OptionalOAuth2PasswordBearer(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        # First try to get the token from the cookie
        token = request.cookies.get("access_token")
        if token:
            return token
            
        # Fall back to standard OAuth2 flow (Authorization header)
        try:
            return await super().__call__(request)
        except HTTPException:
            return None

# Use the optional scheme for the optional dependency
optional_oauth2_scheme = OptionalOAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user_optional(
    db: Session = Depends(get_db), token: Optional[str] = Depends(optional_oauth2_scheme)
) -> Optional[Any]:
    """Get current user or None if not authenticated"""
    from app.db.models import User
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            return None
    except (jwt.JWTError, ValidationError):
        return None
        
    user = db.query(User).filter(User.email == token_data.sub).first()
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[Any]:
    """Authenticate user by email and password"""
    from app.db.models import User
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def generate_secret_key(length: int = 64) -> str:
    """Generate a cryptographically secure random key.
    
    Args:
        length: The minimum length of the key in bytes (default 64)
        
    Returns:
        A secure random string suitable for use as a SECRET_KEY
    """
    return secrets.token_urlsafe(length)


def generate_reset_token() -> str:
    """Generate a unique reset token for password recovery.
    
    Returns:
        A secure random string suitable for password reset
    """
    return f"{uuid.uuid4().hex}{secrets.token_urlsafe(16)}"


def get_reset_token_expiry() -> datetime:
    """Get expiry datetime for reset tokens.
    
    Returns:
        Datetime when the token should expire (24 hours from now)
    """
    return datetime.utcnow() + timedelta(hours=24)


if __name__ == "__main__":
    # Generate a new secret key when this module is run directly
    print("\n=== GENERATING NEW SECRET KEY ===")
    print(f"\nAdd this to your .env file:")
    print(f"API_SECRET_KEY={generate_secret_key()}")
    print("\nWARNING: Keep this key secure and never commit it to version control!")
    print("===============================\n")