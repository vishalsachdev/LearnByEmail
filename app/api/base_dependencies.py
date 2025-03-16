"""
Base dependencies for API routes.

This module provides common dependencies for the API routes, including CSRF protection.
"""

from fastapi import Request, HTTPException, status
from app.core.csrf import validate_csrf_token, CSRF_HEADER_NAME


async def verify_csrf_token(request: Request):
    """Verify CSRF token for API routes."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Skip CSRF verification for non-mutating requests
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
        
    # Get token from header
    token = request.headers.get(CSRF_HEADER_NAME)
    logger.info(f"CSRF header check: {CSRF_HEADER_NAME} = {token[:10] + '...' if token and len(token) > 10 else token}")
    
    # Also check if there's a CSRF token in cookies, for debugging
    csrf_cookie = request.cookies.get("csrf_token")
    if csrf_cookie:
        logger.info(f"CSRF cookie found: {csrf_cookie[:10] + '...' if len(csrf_cookie) > 10 else csrf_cookie}")
    else:
        logger.info("No CSRF cookie found")
    
    # If no token or invalid token, raise exception
    if not token:
        logger.warning("CSRF token missing in request headers")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing from request headers"
        )
        
    if not validate_csrf_token(token):
        logger.warning(f"CSRF token validation failed for token: {token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token is invalid or expired"
        )