"""
CSRF Protection Module for LearnByEmail application.

This module provides functions for generating and validating CSRF tokens
to protect against Cross-Site Request Forgery attacks.
"""

import secrets
import time
import hmac
import hashlib
from typing import Optional, Tuple
from fastapi import Request, Response, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

# Constants
CSRF_TOKEN_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"
# Token expiry in seconds (30 minutes)
CSRF_TOKEN_EXPIRY = 1800


def generate_csrf_token(prefix: str = "csrf") -> str:
    """
    Generate a secure CSRF token with timestamp and signature.
    
    Args:
        prefix: Optional prefix to identify token purpose
        
    Returns:
        Secure CSRF token string
    """
    # Generate a random token
    random_token = secrets.token_hex(16)
    # Add timestamp to prevent token reuse
    timestamp = str(int(time.time()))
    # Combine parts
    token_parts = f"{prefix}.{timestamp}.{random_token}"
    # Generate HMAC signature
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        token_parts.encode(),
        hashlib.sha256
    ).hexdigest()
    # Return the full token
    return f"{token_parts}.{signature}"


def validate_csrf_token(token: str) -> bool:
    """
    Validate a CSRF token's format, signature, and expiry.
    
    Args:
        token: CSRF token to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not token:
        return False
        
    try:
        # Split token into parts
        parts = token.split(".")
        if len(parts) != 4:
            return False
            
        prefix, timestamp_str, random_part, signature = parts
        
        # Verify timestamp (token expiry)
        try:
            timestamp = int(timestamp_str)
            current_time = int(time.time())
            if current_time - timestamp > CSRF_TOKEN_EXPIRY:
                return False
        except ValueError:
            return False
            
        # Reconstruct token parts for signature verification
        token_parts = f"{prefix}.{timestamp_str}.{random_part}"
        
        # Calculate expected signature
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode(),
            token_parts.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(signature, expected_signature)
    except Exception:
        return False


async def csrf_protect(request: Request) -> None:
    """
    Dependency for protecting routes against CSRF attacks.
    
    Args:
        request: FastAPI Request object
        
    Raises:
        HTTPException: If CSRF validation fails
    """
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        # Try to get the token from various sources
        token = None
        
        # Check form data
        try:
            form_data = await request.form()
            token = form_data.get(CSRF_FORM_FIELD)
        except Exception:
            pass
            
        # Try headers if not found in form
        if not token:
            token = request.headers.get(CSRF_HEADER_NAME)
            
        # Try cookies if still not found
        if not token:
            token = request.cookies.get(CSRF_COOKIE_NAME)
            
        # Validate token
        if not token or not validate_csrf_token(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing or invalid"
            )


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set CSRF tokens in cookies for all GET requests.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request through middleware."""
        response = await call_next(request)
        
        # Set CSRF cookie for GET requests if not already present
        if request.method == "GET" and isinstance(response, Response):
            csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
            if not csrf_cookie:
                token = generate_csrf_token()
                response.set_cookie(
                    key=CSRF_COOKIE_NAME,
                    value=token,
                    max_age=CSRF_TOKEN_EXPIRY,
                    httponly=True,
                    secure=settings.COOKIE_SECURE,
                    samesite=settings.COOKIE_SAMESITE
                )
                
        return response


def get_csrf_token(request: Request) -> str:
    """
    Get current CSRF token or generate a new one.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        CSRF token string
    """
    # Try to get existing token from cookie
    token = request.cookies.get(CSRF_COOKIE_NAME)
    
    # Generate new token if none exists or existing token is invalid
    if not token or not validate_csrf_token(token):
        token = generate_csrf_token()
        
    return token