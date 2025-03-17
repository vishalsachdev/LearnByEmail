from fastapi import Request, HTTPException, status, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from typing import Callable, Dict, Any
from functools import wraps
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Create a limiter instance that will identify users by their IP address
limiter = Limiter(key_func=get_remote_address)

# Define rate limit error handler
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors
    Returns a 429 status code with a descriptive message
    """
    # Get client IP address
    client_ip = get_remote_address(request)
    
    # Log comprehensive information about this rate limit hit
    log_data = {
        "event": "rate_limit_exceeded",
        "ip": client_ip,
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime.now().isoformat(),
        "limit": str(exc.detail),
        "user_agent": request.headers.get("user-agent", "unknown"),
        "referer": request.headers.get("referer", "unknown"),
    }
    
    # Get current user if authenticated
    auth_header = request.cookies.get("access_token")
    if auth_header:
        log_data["authenticated"] = True
    else:
        log_data["authenticated"] = False
    
    # Log as a warning
    logger.warning(f"Rate limit exceeded: {log_data}")
    
    # For repeated offenders, we could implement more sophisticated blocking
    
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded. Please try again later. Limit: {exc.detail}"
    )

# Function to configure rate limiting in a FastAPI app
def configure_rate_limiting(app):
    """Configure rate limiting for the FastAPI application"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Dependency for strict rate limiting (most protected endpoints)
def strict_rate_limit():
    """
    Apply strict rate limiting - 10 requests per minute, 100 per hour
    Use for sensitive endpoints like authentication, registration, password reset
    """
    @limiter.limit("10/minute;100/hour")
    def limit_request(request: Request):
        return request
    
    return limit_request

# Dependency for standard rate limiting (normal endpoints)
def standard_rate_limit():
    """
    Apply standard rate limiting - 30 requests per minute, 300 per hour
    Use for general API endpoints
    """
    @limiter.limit("30/minute;300/hour")
    def limit_request(request: Request):
        return request
    
    return limit_request

# Helper decorator for applying rate limiting to non-endpoint functions
def rate_limited(limit_string: str):
    """
    Decorator to apply rate limiting to any function that takes a Request
    Example: @rate_limited("5/minute")
    """
    def decorator(func: Callable):
        @limiter.limit(limit_string)
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator