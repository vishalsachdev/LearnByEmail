from fastapi import FastAPI, Depends, Request, Response, Form, Cookie, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from typing import List, Tuple, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import asyncio
from starlette.middleware.sessions import SessionMiddleware
import re
import urllib.parse

from app.core.config import settings
from app.db.session import get_db, engine
from app.db.models import Base, User, Subscription
from app.api import auth, subscriptions, content_preview
from app.services.scheduler import start_scheduler, init_scheduler_jobs
from app.core.security import get_current_user_optional, authenticate_user, create_access_token, get_current_user
from app.core.csrf import CSRFMiddleware, csrf_protect, get_csrf_token, CSRF_FORM_FIELD

# Setup logging
import os
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for LearnByEmail - Daily educational content via email",
    version="0.1.0",
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add session middleware for flash messages
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    max_age=3600,  # 1 hour
    same_site=settings.COOKIE_SAMESITE,  # Use same SameSite policy as auth cookies
    https_only=settings.COOKIE_SECURE,   # Secure flag for HTTPS
)

# Add CSRF protection middleware
app.add_middleware(CSRFMiddleware)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


# Add custom middleware to modify templates
@app.middleware("http")
async def add_template_globals(request: Request, call_next):
    # Store request in template context
    templates.env.globals["request"] = request
    templates.env.globals["csrf_token"] = get_csrf_token(request)
    templates.env.globals["csrf_field"] = CSRF_FORM_FIELD
    
    # We will add flash messages in the route handlers
    # NOT in middleware to avoid initialization order issues
    response = await call_next(request)
    return response


# Helper function to add flash messages
def flash(request: Request, message: str, category: str = "info"):
    # Safely initialize flash messages
    try:
        flash_messages = request.session.get("flash_messages", [])
        flash_messages.append((category, message))
        request.session["flash_messages"] = flash_messages
    except Exception as e:
        logger.error(f"Error adding flash message: {e}")


# Custom Jinja2 functions
def get_flashed_messages(request: Request, with_categories=False):
    """Get and clear flash messages from session"""
    try:
        messages = request.session.get("flash_messages", [])
        request.session["flash_messages"] = []
        
        if with_categories:
            return messages  # Already in (category, message) format
        else:
            return [message for _, message in messages]  # Return only messages
    except Exception as e:
        logger.error(f"Error getting flash messages: {e}")
        return []


def url_for(name: str, **path_params) -> str:
    """Simple URL generator to replace Flask's url_for"""
    paths = {
        "home": "/",
        "login": "/login",
        "register": "/register",
        "register_page": "/register",
        "register_submit": "/register",
        "dashboard": "/dashboard",
        "logout": "/logout",
        "subscribe": "/subscribe",
        "static": "/static",
        "forgot_password_page": "/forgot-password",
        "reset_password_page": "/reset-password",
        "login_page": "/login",
        "login_submit": "/login", 
        "bulk_subscription_action": "/bulk-subscription-action",
        "about_page": "/about",
        "privacy_page": "/privacy",
        "terms_page": "/terms",
        "contact_page": "/contact"
    }
    
    url = paths.get(name, "/")
    
    # Special case for static files
    if name == "static" and "filename" in path_params:
        url = f"{url}/{path_params['filename']}"

    # Special case for edit_subscription_page
    if name == "edit_subscription_page" and "subscription_id" in path_params:
        url = f"/edit-subscription/{path_params['subscription_id']}"
    
    # Special case for delete_subscription
    if name == "delete_subscription" and "subscription_id" in path_params:
        url = f"/delete-subscription/{path_params['subscription_id']}"

    # Add query params for reset-password
    if name == "reset_password_page" and "token" in path_params:
        url = f"{url}?token={path_params['token']}"
        
    return url


# Create a wrapper for get_flashed_messages that doesn't require request parameter in templates
def get_flashed_messages_wrapper(with_categories=False):
    """Template-friendly wrapper for get_flashed_messages that gets request from context"""
    request = templates.env.globals.get("request")
    if not request:
        return []
    return get_flashed_messages(request, with_categories)

# Add custom functions to Jinja2 templates
templates.env.globals["get_flashed_messages"] = get_flashed_messages_wrapper
templates.env.globals["url_for"] = url_for
templates.env.filters["urlencode"] = lambda u: urllib.parse.quote(u)


# Include API routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"],
)

app.include_router(
    subscriptions.router,
    prefix=f"{settings.API_V1_STR}/subscriptions",
    tags=["subscriptions"],
)

app.include_router(
    content_preview.router,
    prefix=f"{settings.API_V1_STR}/preview",
    tags=["preview"],
)


# Create static and templates directories if they don't exist
import os
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Validate topic function
def validate_topic(topic, request, current_user, template_name="index.html", template_context=None):
    """Validate topic and return response if invalid"""
    context = template_context or {"request": request, "current_user": current_user}
    
    # Check minimum length
    if len(topic.strip()) < 3:
        flash(request, "Topic must be at least 3 characters long", "danger")
        if current_user:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return templates.TemplateResponse(template_name, context)
    
    # Check if topic contains only valid characters
    if not re.match(r'^[A-Za-z0-9\s\-_,.&+\'()]+$', topic):
        flash(request, "Topic contains invalid characters. Please use only letters, numbers, spaces, and common punctuation.", "danger")
        if current_user:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return templates.TemplateResponse(template_name, context)
    
    # Check maximum length
    if len(topic) > 50:
        flash(request, "Topic must be less than 50 characters", "danger")
        if current_user:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return templates.TemplateResponse(template_name, context)
    
    # Topic is valid
    return None


# Front-end routes (HTML responses)
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Home page"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "current_user": current_user}
    )


@app.get("/about", response_class=HTMLResponse)
async def about_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """About Us page"""
    return templates.TemplateResponse(
        "about.html",
        {"request": request, "current_user": current_user}
    )


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Privacy Policy page"""
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request, "current_user": current_user}
    )


@app.get("/terms", response_class=HTMLResponse)
async def terms_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Terms of Service page"""
    return templates.TemplateResponse(
        "terms.html",
        {"request": request, "current_user": current_user}
    )


@app.get("/contact", response_class=HTMLResponse)
async def contact_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Contact page"""
    return templates.TemplateResponse(
        "contact.html",
        {"request": request, "current_user": current_user}
    )


@app.post("/subscribe", response_class=HTMLResponse, dependencies=[Depends(csrf_protect)])
async def subscribe(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    topic: str = Form(...),
    preferred_time: str = Form(...),
    timezone: str = Form(...),
    difficulty: str = Form(default="medium"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Handle subscription form submission"""
    # Validate input
    if not email or not topic or not preferred_time or not timezone:
        flash(request, "All fields are required", "danger")
        if current_user:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return templates.TemplateResponse(
                "index.html", 
                {"request": request, "current_user": current_user}
            )
            
    # Validate topic
    invalid_response = validate_topic(
        topic, 
        request, 
        current_user, 
        "index.html", 
        {"request": request, "current_user": current_user}
    )
    if invalid_response:
        return invalid_response
    
    # Parse preferred time
    try:
        time_parts = preferred_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        preferred_time_obj = datetime.now().replace(hour=hour, minute=minute).time()
    except (ValueError, IndexError):
        flash(request, "Invalid time format", "danger")
        if current_user:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return templates.TemplateResponse(
                "index.html", 
                {"request": request, "current_user": current_user}
            )
    
    # If user is not logged in, we need to create or get a user account
    if not current_user:
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Create temporary user with random password
            import secrets
            temp_password = secrets.token_urlsafe(12)
            user = User(
                email=email,
                password_hash=User.get_password_hash(temp_password)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        user_id = user.id
    else:
        user_id = current_user.id
    
    # Check if subscription already exists
    existing = db.query(Subscription).filter(
        Subscription.email == email,
        Subscription.topic == topic,
        Subscription.user_id == user_id
    ).first()
    
    if existing:
        flash(request, "You are already subscribed to this topic", "warning")
        if current_user:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return templates.TemplateResponse(
                "index.html", 
                {"request": request, "current_user": current_user}
            )
    
    # Validate difficulty level
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "medium"  # Default to medium if invalid
    
    # Create subscription
    subscription = Subscription(
        email=email,
        topic=topic,
        preferred_time=preferred_time_obj,
        timezone=timezone,
        difficulty=difficulty,
        user_id=user_id
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    # Schedule email job
    from app.services.scheduler import add_email_job
    add_email_job(subscription)
    
    # Send an immediate first email
    from app.services.email_sender import send_educational_email_task
    try:
        # Use background_tasks to handle the asyncio coroutine properly
        background_tasks = BackgroundTasks()
        background_tasks.add_task(send_educational_email_task, int(subscription.id))
        logger.info(f"Scheduled immediate welcome email for new subscription {subscription.id} to {email}")
    except Exception as e:
        logger.error(f"Error scheduling welcome email: {str(e)}")
    
    # Success message - different for logged in vs anonymous users
    if current_user:
        flash(request, f"Subscription to {topic} confirmed! You'll receive your first email shortly.", "success")
    else:
        # Enhanced message for non-logged in users with registration prompt
        flash(request, f"Subscription to {topic} confirmed! You'll receive your first email shortly. <a href='/register?email={urllib.parse.quote(email)}' class='alert-link'>Create an account</a> to manage your subscriptions and customize delivery preferences.", "success")
    
    # Always redirect to dashboard if logged in, otherwise show index page
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        # For non-logged in users, set a flag to show registration prompt
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "current_user": None,
                "show_registration_prompt": True,
                "subscription_email": email,
                "subscription_topic": topic
            }
        )


@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, 
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Login page"""
    if current_user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "current_user": current_user}
    )


@app.post("/login", response_class=HTMLResponse, dependencies=[Depends(csrf_protect)])
async def login_submit(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login form submission"""
    user = authenticate_user(db, email, password)
    if not user:
        flash(request, "Invalid email or password", "danger")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "current_user": None}
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.email, 
        expires_delta=access_token_expires
    )
    
    # Set cookie with token (no Bearer prefix)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,  # Just the raw token, not "Bearer {token}"
        httponly=True,
        secure=settings.COOKIE_SECURE,  # True in production/https environments
        samesite=settings.COOKIE_SAMESITE,  # 'lax' or 'strict'
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request, 
    email: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Registration page"""
    if current_user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(
        "register.html", 
        {"request": request, "current_user": current_user, "prefill_email": email}
    )


@app.post("/register", response_class=HTMLResponse, dependencies=[Depends(csrf_protect)])
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle registration form submission"""
    # Validate input
    if not email or not password:
        flash(request, "Email and password are required", "danger")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "current_user": None}
        )
    
    if password != confirm_password:
        flash(request, "Passwords do not match", "danger")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "current_user": None}
        )
    
    # Check if user already exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        flash(request, "Email already registered", "danger")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "current_user": None}
        )
    
    # Create user
    new_user = User(
        email=email,
        password_hash=User.get_password_hash(password)
    )
    
    db.add(new_user)
    db.commit()
    
    flash(request, "Registration successful! Please log in.", "success")
    return RedirectResponse(url="/login", status_code=303)


@app.get("/logout")
async def logout():
    """Log out user by deleting token cookie"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(
        key="access_token",
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        httponly=True
    )
    return response


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Forgot password page"""
    if current_user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request, "current_user": current_user}
    )


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(
    request: Request,
    token: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Reset password page"""
    if current_user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "current_user": current_user, "token": token}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """User dashboard"""
    if not current_user:
        flash(request, "Please log in to access the dashboard", "warning")
        return RedirectResponse(url="/login", status_code=303)
    
    # Get user's subscriptions
    subscriptions = db.query(Subscription).filter(Subscription.user_id == current_user.id).all()
    
    # Convert last_sent times from UTC to each subscription's timezone
    from datetime import datetime
    import pytz
    
    for subscription in subscriptions:
        if subscription.last_sent:
            # The last_sent is stored in UTC
            utc_time = subscription.last_sent.replace(tzinfo=pytz.UTC)
            
            try:
                # Convert to subscription's timezone
                local_tz = pytz.timezone(str(subscription.timezone))
                local_time = utc_time.astimezone(local_tz)
                
                # Store the converted time for display
                subscription.local_last_sent = local_time
            except Exception as e:
                logger.error(f"Error converting timezone: {e}")
                # If conversion fails, just use UTC time
                subscription.local_last_sent = utc_time
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "current_user": current_user,
            "subscriptions": subscriptions
        }
    )


@app.get("/edit-subscription/{subscription_id}", response_class=HTMLResponse)
async def edit_subscription_page(
    request: Request,
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Edit subscription page"""
    if not current_user:
        flash(request, "Please log in to edit subscriptions", "warning")
        return RedirectResponse(url="/login", status_code=303)
    
    # Get subscription
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        flash(request, "Subscription not found", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    return templates.TemplateResponse(
        "edit_subscription.html", 
        {
            "request": request, 
            "current_user": current_user,
            "subscription": subscription
        }
    )


@app.post("/edit-subscription/{subscription_id}", response_class=HTMLResponse, dependencies=[Depends(csrf_protect)])
async def edit_subscription_submit(
    request: Request,
    subscription_id: int,
    topic: str = Form(None),
    preferred_time: str = Form(None),
    timezone: str = Form(None),
    difficulty: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Handle edit subscription form submission"""
    if not current_user:
        flash(request, "Please log in to edit subscriptions", "warning")
        return RedirectResponse(url="/login", status_code=303)
    
    # Get subscription
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        flash(request, "Subscription not found", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Update fields
    if topic:
        # Validate topic
        template_context = {
            "request": request, 
            "current_user": current_user,
            "subscription": subscription
        }
        invalid_response = validate_topic(
            topic, 
            request, 
            current_user, 
            "edit_subscription.html", 
            template_context
        )
        if invalid_response:
            return invalid_response
        
        db.query(Subscription).filter(Subscription.id == subscription.id).update(
            {"topic": topic}
        )
        
    if preferred_time:
        try:
            time_parts = preferred_time.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            new_time = datetime.now().replace(hour=hour, minute=minute).time()
            db.query(Subscription).filter(Subscription.id == subscription.id).update(
                {"preferred_time": new_time}
            )
        except (ValueError, IndexError):
            flash(request, "Invalid time format", "danger")
            return templates.TemplateResponse(
                "edit_subscription.html", 
                {
                    "request": request, 
                    "current_user": current_user,
                    "subscription": subscription
                }
            )
    
    if timezone:
        db.query(Subscription).filter(Subscription.id == subscription.id).update(
            {"timezone": timezone}
        )
    
    if difficulty:
        # Validate difficulty level
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "medium"  # Default to medium if invalid
            
        db.query(Subscription).filter(Subscription.id == subscription.id).update(
            {"difficulty": difficulty}
        )
    
    db.commit()
    
    # Update scheduler job
    from app.services.scheduler import remove_email_job, add_email_job
    remove_email_job(int(subscription.id))
    add_email_job(subscription)
    
    flash(request, "Subscription updated successfully", "success")
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/delete-subscription/{subscription_id}", dependencies=[Depends(csrf_protect)])
async def delete_subscription(
    request: Request,
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete subscription"""
    if not current_user:
        flash(request, "Please log in to delete subscriptions", "warning")
        return RedirectResponse(url="/login", status_code=303)
    
    # Get subscription
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        flash(request, "Subscription not found", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Remove scheduler job
    from app.services.scheduler import remove_email_job
    remove_email_job(int(subscription.id))
    
    try:
        # Delete email history records first to avoid foreign key constraint issues
        from app.db.models import EmailHistory
        
        # Delete all related email history records
        db.query(EmailHistory).filter(EmailHistory.subscription_id == subscription.id).delete()
        
        # Then delete the subscription
        db.delete(subscription)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting subscription: {str(e)}")
        flash(request, f"Error deleting subscription: {str(e)}", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    flash(request, "Subscription deleted successfully", "success")
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/bulk-subscription-action", dependencies=[Depends(csrf_protect)])
async def bulk_subscription_action(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Handle bulk actions on subscriptions"""
    if not current_user:
        flash(request, "Please log in to manage subscriptions", "warning")
        return RedirectResponse(url="/login", status_code=303)
    
    # Get form data
    form_data = await request.form()
    action = form_data.get("action")
    subscription_ids = form_data.getlist("subscription_ids")
    
    if not action or not subscription_ids:
        flash(request, "No action or subscriptions selected", "warning")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Convert subscription IDs to integers
    try:
        # Convert list items to integers, handling UploadFile objects if present
        int_subscription_ids: List[int] = []
        for id_item in subscription_ids:
            if hasattr(id_item, 'strip'):  # Check if it's a string
                int_subscription_ids.append(int(id_item))
            else:
                # Handle other types as needed (like UploadFile)
                # First convert to string safely, then to int
                try:
                    string_value = str(id_item)
                    int_subscription_ids.append(int(string_value))
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert value to int: {id_item}")
                    # Skip invalid values
        # Create a new variable with the proper type
        id_list = int_subscription_ids
    except ValueError:
        flash(request, "Invalid subscription selection", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Get subscriptions that belong to the current user
    subscriptions = db.query(Subscription).filter(
        Subscription.id.in_(id_list),
        Subscription.user_id == current_user.id
    ).all()
    
    if not subscriptions:
        flash(request, "No valid subscriptions selected", "warning")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Process based on action
    from app.services.scheduler import remove_email_job, add_email_job
    count = len(subscriptions)
    
    if action == "delete":
        # Check for confirmation
        if not form_data.get("confirm_delete"):
            flash(request, "Please confirm deletion", "warning")
            return RedirectResponse(url="/dashboard", status_code=303)
        
        # Remove scheduler jobs and delete subscriptions
        try:
            from app.db.models import EmailHistory
            
            for subscription in subscriptions:
                # Remove scheduler job
                remove_email_job(int(subscription.id))
                
                # Delete email history records for this subscription
                db.query(EmailHistory).filter(EmailHistory.subscription_id == subscription.id).delete()
                
                # Delete the subscription
                db.delete(subscription)
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error performing bulk deletion: {str(e)}")
            flash(request, f"Error deleting subscriptions: {str(e)}", "danger")
            return RedirectResponse(url="/dashboard", status_code=303)
        flash(request, f"Successfully deleted {count} subscriptions", "success")
    
    elif action == "change_time":
        preferred_time = form_data.get("preferred_time")
        if not preferred_time:
            flash(request, "Please provide a new delivery time", "warning")
            return RedirectResponse(url="/dashboard", status_code=303)
            
        # Handle UploadFile or string
        if hasattr(preferred_time, 'read'):  # It's an UploadFile
            preferred_time_str = str(preferred_time)
        else:
            preferred_time_str = preferred_time
        
        try:
            # Parse time string
            from datetime import datetime
            time_parts = preferred_time_str.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            preferred_time_obj = datetime.now().replace(hour=hour, minute=minute).time()
            
            # Update subscriptions
            for subscription in subscriptions:
                # Remove old job first
                remove_email_job(int(subscription.id))
                
                # Update time using a query to avoid type issues
                db.query(Subscription).filter(Subscription.id == subscription.id).update(
                    {"preferred_time": preferred_time_obj}
                )
                
                # Add new job
                add_email_job(subscription)
            
            db.commit()
            flash(request, f"Successfully updated delivery time for {count} subscriptions", "success")
        
        except (ValueError, IndexError) as e:
            logger.error(f"Error updating time: {str(e)}")
            flash(request, "Invalid time format", "danger")
    
    elif action == "change_timezone":
        timezone = form_data.get("timezone")
        if not timezone:
            flash(request, "Please provide a new timezone", "warning")
            return RedirectResponse(url="/dashboard", status_code=303)
            
        # Handle UploadFile or string
        if hasattr(timezone, 'read'):  # It's an UploadFile
            timezone_str = str(timezone)
        else:
            timezone_str = timezone
        
        # Update subscriptions
        for subscription in subscriptions:
            # Remove old job first
            remove_email_job(int(subscription.id))
            
            # Update timezone
            db.query(Subscription).filter(Subscription.id == subscription.id).update(
                {"timezone": timezone_str}
            )
            
            # Add new job
            add_email_job(subscription)
        
        db.commit()
        flash(request, f"Successfully updated timezone for {count} subscriptions", "success")
    
    else:
        flash(request, "Unknown action", "danger")
    
    return RedirectResponse(url="/dashboard", status_code=303)


# Test route for sending emails immediately
@app.get("/test-email/{subscription_id}")
async def test_email(
    subscription_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Test route to send an email immediately for a subscription"""
    if not current_user:
        flash(request, "Please log in to test email sending", "warning")
        return RedirectResponse(url="/login", status_code=303)
    
    # Get subscription and verify ownership
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        flash(request, "Subscription not found", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    try:
        # Send email
        from app.services.email_sender import send_educational_email_task
        logger.info(f"Attempting to send test email for subscription {subscription_id} to {subscription.email}")
        
        # Run task in background
        from app.core.config import settings
        
        # Use background tasks to properly handle the async operation
        background_tasks.add_task(send_educational_email_task, int(subscription.id))
        flash(request, "Test email sending initiated. Check your inbox shortly!", "success")
    except Exception as e:
        logger.error(f"Error in test email route: {type(e).__name__}: {str(e)}")
        flash(request, f"Error: {str(e)}", "danger")
    
    return RedirectResponse(url="/dashboard", status_code=303)


# Check environment variables - Admin only
@app.get("/check-env")
async def check_env(current_user: User = Depends(get_current_user)):
    """Check environment variables (admin only)"""
    # Only allow admin access (first check if is_admin exists, if not, restrict to no one)
    try:
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            logger.warning(f"Unauthorized attempt to access /check-env by user {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
            
        from app.core.config import settings
        
        # Don't show full API keys, only status and partial key
        def mask_api_key(key: str) -> str:
            if not key:
                return "Not Set"
            return f"Set (ends with ...{key[-4:]})"
            
        env_vars = {
            "SENDGRID_API_KEY": mask_api_key(settings.SENDGRID_API_KEY),
            "SENDGRID_FROM_EMAIL": settings.SENDGRID_FROM_EMAIL,
            "GEMINI_API_KEY": mask_api_key(settings.GEMINI_API_KEY),
            "DATABASE_URL": settings.DATABASE_URL.split("://")[0] + "://******" 
            if "://" in settings.DATABASE_URL else "********"
        }
        
        html = "<h1>Environment Variables</h1><ul>"
        for key, value in env_vars.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        
        logger.info(f"Admin user {current_user.email} accessed environment variables")
        return HTMLResponse(html)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error checking environment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking environment configuration"
        )


# Direct email test route (admin only, own email only)
@app.get("/admin/test-email")
async def direct_test_email(
    current_user: User = Depends(get_current_user)
):
    """Test route to attempt a test email to the current admin user"""
    try:
        # Admin access check
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            logger.warning(f"Unauthorized attempt to access email test by user {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
            
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        from app.core.config import settings
        
        # Only allow sending to the logged-in admin's email
        email = current_user.email
        
        # Send direct test email
        logger.info(f"Admin sending test email to self: {email}")
        
        # Create and send a simple message
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=email,
            subject="LearnByEmail Admin Test Email",
            html_content="<p>This is a test email from LearnByEmail to verify email sending functionality.</p>"
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        status_code = response.status_code
        logger.info(f"SendGrid admin test response: Status {status_code}")
        
        return HTMLResponse(f"<h1>Test email sent to {email}</h1><p>Status code: {status_code}</p>")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Admin test email error: {type(e).__name__}: {str(e)}")
        # Don't expose detailed error messages
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending test email. Check server logs for details."
        )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Startup event handler to initialize scheduler and jobs"""
    logger.info("Starting up application...")
    
    # Check for secure SECRET_KEY
    try:
        if len(settings.API_SECRET_KEY) < 32:
            logger.warning("SECURITY RISK: API_SECRET_KEY is too short. It should be at least 32 characters.")
            logger.warning("Generate a more secure key with: python -m app.core.security")
    except Exception as e:
        logger.critical(f"SECURITY RISK: {str(e)}")
        logger.critical("Generate a new key with: python -m app.core.security")
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise RuntimeError("CRITICAL: Cannot start in production without valid API_SECRET_KEY")
    
    init_scheduler_jobs()
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler to clean up resources"""
    logger.info("Shutting down application...")