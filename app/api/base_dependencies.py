"""
Base dependencies for API routes.

This module provides common dependencies for the API routes, including CSRF protection.
"""

from fastapi import Request, HTTPException, status
from app.core.csrf import validate_csrf_token, CSRF_HEADER_NAME


async def verify_csrf_token(request: Request):
    """Verify CSRF token for API routes."""
    # Skip CSRF verification for non-mutating requests
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
        
    # Get token from header
    token = request.headers.get(CSRF_HEADER_NAME)
    
    # If no token or invalid token, raise exception
    if not token or not validate_csrf_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid"
        )