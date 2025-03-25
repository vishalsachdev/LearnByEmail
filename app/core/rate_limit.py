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
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors
    Returns a template response for HTML endpoints and JSON for API endpoints
    """
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.templating import Jinja2Templates
    
    # Get client IP address
    client_ip = get_remote_address(request)
    
    # Log the rate limit hit
    logger.warning(f"Rate limit exceeded: IP={client_ip}, Path={request.url.path}")
    
    # Check if this is an HTML route (by Accept header or URL path)
    accept_header = request.headers.get("accept", "")
    is_html_route = ("text/html" in accept_header) or (request.url.path in ["/subscribe", "/login", "/register"])
    
    if is_html_route:
        # For HTML routes, flash a message and redirect back
        templates = Jinja2Templates(directory="app/templates")
        
        # Add flash message to session
        if not hasattr(request, "session"):
            request.session = {}
        flash_messages = request.session.get("flash_messages", [])
        flash_messages.append(("danger", "Too many requests. Please try again later."))
        request.session["flash_messages"] = flash_messages
        
        # Return to previous page or home
        referer = request.headers.get("referer")
        redirect_url = referer if referer else "/"
        
        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url=redirect_url,
            status_code=303
        )
    else:
        # For API routes, return JSON response
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please try again later."}
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