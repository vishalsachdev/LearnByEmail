import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
import urllib.parse
import asyncio
from smtplib import SMTPAuthenticationError, SMTPException

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Subscription, EmailHistory, User
from app.core.config import settings
from app.services.content_generator import generate_educational_content

# Try to import SendGrid if available
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    logging.warning("SendGrid package not available. Email sending will use SMTP only.")
    SENDGRID_AVAILABLE = False

logger = logging.getLogger(__name__)


async def check_email_credentials():
    """Check if email credentials are properly configured"""
    # First check if SendGrid is configured
    sendgrid_key = settings.SENDGRID_API_KEY
    if sendgrid_key:
        logger.info("SendGrid API key is configured")
        return settings.SENDGRID_FROM_EMAIL, "sendgrid"
        
    # Fall back to SMTP
    username = settings.GMAIL_USERNAME
    password = settings.GMAIL_APP_PASSWORD
    
    if not username or not password:
        logger.error("No email credentials configured. Please set either SENDGRID_API_KEY or GMAIL_USERNAME+GMAIL_APP_PASSWORD")
        # Return default values to prevent errors, but emails won't be sent
        return "noreply@example.com", None
        
    logger.info(f"Using GMAIL credentials for {username}")
    return username, password


async def create_html_email(subject, content, to_email, email_type="educational"):
    """Create HTML email message"""
    from_email, _ = await check_email_credentials()
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['Subject'] = subject
    msg['To'] = to_email

    if email_type == "reset_password":
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ font-size: 24px; margin-bottom: 20px; }}
                p {{ margin: 15px 0; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #1a73e8; color: white; 
                          text-decoration: none; border-radius: 4px; font-weight: bold; }}
                .footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <h1>Password Reset Request</h1>
            <p>You requested to reset your password for your LearnByEmail account.</p>
            <p>Click the button below to reset your password:</p>
            <p><a href="{content}" class="button">Reset Password</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{content}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't request this password reset, you can safely ignore this email.</p>
            <div class="footer">
                <p>&copy; 2025 LearnByEmail. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    elif email_type == "confirmation":
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ font-size: 24px; margin-bottom: 20px; }}
                p {{ margin: 15px 0; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #1a73e8; color: white; 
                          text-decoration: none; border-radius: 4px; font-weight: bold; }}
                .footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <h1>Confirm Your Email Address</h1>
            <p>Thank you for registering with LearnByEmail! To start receiving educational content, please confirm your email address.</p>
            <p>Click the button below to confirm your email:</p>
            <p><a href="{content}" class="button">Confirm Email</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{content}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't sign up for LearnByEmail, you can safely ignore this email.</p>
            <div class="footer">
                <p>&copy; 2025 LearnByEmail. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    else:
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ font-size: 24px; margin-bottom: 20px; }}
                h2 {{ font-size: 20px; margin-top: 25px; }}
                p {{ margin: 15px 0; }}
                pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; margin: 15px 0; }}
                code {{ font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5; }}
                .language-python {{ color: #333; }}
                .language-python .keyword {{ color: #0000FF; }}
                .language-python .number {{ color: #008000; }}
                .language-python .string {{ color: #A31515; }}
                .language-python .comment {{ color: #008000; font-style: italic; }}
                .footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <h1>Your Daily Educational Content</h1>
            {content}
            <div class="footer">
                <p>You received this email because you subscribed to daily educational content.
                To unsubscribe, reply with 'UNSUBSCRIBE' in the subject line.</p>
            </div>
        </body>
        </html>
        """
    msg.attach(MIMEText(body, 'html'))
    return msg


async def send_via_sendgrid(to_email, subject, html_content):
    """Send email using SendGrid API"""
    if not SENDGRID_AVAILABLE:
        logger.error("SendGrid package not available but send_via_sendgrid was called")
        return False

    try:
        sendgrid_key = settings.SENDGRID_API_KEY
        if not sendgrid_key:
            logger.error("SENDGRID_API_KEY not set")
            return False

        # Just use the email address without a fancy display name to avoid spam filters
        from_email = settings.SENDGRID_FROM_EMAIL
        
        logger.info(f"Attempting to send email via SendGrid to {to_email}")
        
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        sg = SendGridAPIClient(sendgrid_key)
        # Send message
        
        try:
            response = await asyncio.to_thread(sg.send, message)
            
            status_code = response.status_code
            logger.info(f"SendGrid Response: Status {status_code}")
            
            if status_code >= 200 and status_code < 300:
                logger.info("Email sent successfully via SendGrid")
                return True
            else:
                logger.error(f"SendGrid API error: Status code {status_code}")
                # Avoid logging potentially sensitive response bodies
                logger.error("Check SendGrid dashboard for detailed error information")
                return False
        except Exception as send_error:
            # Log only error type, not the full exception which might contain API keys
            error_type = type(send_error).__name__
            logger.error(f"SendGrid send error: {error_type}")
            if hasattr(send_error, 'body') and send_error.body:
                logger.error("SendGrid returned an error response. Check dashboard for details.")
            return False

    except Exception as e:
        # Log only the error type to avoid exposing API keys in logs
        error_type = type(e).__name__
        logger.error(f"SendGrid initialization error: {error_type}")
        logger.error("Check your SendGrid configuration and API key validity")
        return False


async def send_via_smtp(to_email, subject, html_content):
    """Send email using SMTP (Gmail)"""
    try:
        username, password = await check_email_credentials()
        
        # If no valid credentials, log error and return
        if password is None:
            logger.error("No valid SMTP credentials available")
            return False
            
        msg = await create_html_email(subject, html_content, to_email)

        logger.info(f"Attempting to send email via SMTP to {to_email}")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            # Log before sensitive operation with masked credentials
            logger.info(f"Authenticating with Gmail SMTP using account: {username}")
            # Actual login with real password
            server.login(username, password)
            server.send_message(msg)
            
        logger.info(f"Successfully sent email via SMTP to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Error: Failed to authenticate with Gmail")
        logger.error("Check your GMAIL_USERNAME and GMAIL_APP_PASSWORD environment variables")
        return False
    except Exception as e:
        # Log only error type to avoid potentially exposing credentials
        error_type = type(e).__name__
        logger.error(f"SMTP Error: {error_type}")
        logger.error("Check your SMTP configuration and credentials")
        return False


async def send_password_reset_email(email: str, token: str):
    """Send password reset email to user"""
    try:
        # Create reset link
        reset_url = f"{settings.BASE_URL}/reset-password?token={token}"
        
        logger.info(f"Sending password reset email to {email}")
        
        # Check which email provider is available
        email_provider_available = False
        
        # Try SendGrid first
        sent = False
        if SENDGRID_AVAILABLE and settings.SENDGRID_API_KEY:
            email_provider_available = True
            logger.info(f"Attempting to send password reset email via SendGrid to {email}")
            
            # Create HTML content for the password reset email
            msg = await create_html_email(
                "Reset Your LearnByEmail Password",
                reset_url,
                email,
                email_type="reset_password"
            )
            
            # Send email using SendGrid
            sent = await send_via_sendgrid(
                email,
                "Reset Your LearnByEmail Password",
                msg.get_payload()[0].get_payload()
            )
            
            if sent:
                logger.info(f"Successfully sent password reset email via SendGrid to {email}")
            else:
                logger.error(f"SendGrid password reset email sending failed for {email}")
        
        # Fall back to SMTP if SendGrid failed or not available
        if not sent:
            if settings.GMAIL_USERNAME and settings.GMAIL_APP_PASSWORD:
                email_provider_available = True
                logger.info(f"Attempting to send password reset email via SMTP to {email}")
                sent = await send_via_smtp(
                    email,
                    "Reset Your LearnByEmail Password",
                    reset_url
                )
                
                if sent:
                    logger.info(f"Successfully sent password reset email via SMTP to {email}")
                else:
                    logger.error(f"SMTP password reset email sending failed for {email}")
                    
        if not email_provider_available:
            logger.error("No email provider credentials configured. Cannot send password reset email.")
            
        return sent
    
    except Exception as e:
        logger.error(f"Error sending password reset email: {type(e).__name__}: {str(e)}")
        return False


async def send_confirmation_email(email: str, token: str):
    """Send email confirmation link to user"""
    try:
        # Create confirmation link
        confirmation_url = f"{settings.BASE_URL}/confirm-email?token={token}"
        
        logger.info(f"Sending email confirmation to {email}")
        
        # Check which email provider is available
        email_provider_available = False
        
        # Try SendGrid first
        sent = False
        if SENDGRID_AVAILABLE and settings.SENDGRID_API_KEY:
            email_provider_available = True
            logger.info(f"Attempting to send confirmation email via SendGrid to {email}")
            
            # Create HTML content for the confirmation email
            msg = await create_html_email(
                "Confirm Your LearnByEmail Account",
                confirmation_url,
                email,
                email_type="confirmation"
            )
            
            # Send email using SendGrid
            sent = await send_via_sendgrid(
                email,
                "Confirm Your LearnByEmail Account",
                msg.get_payload()[0].get_payload()
            )
            
            if sent:
                logger.info(f"Successfully sent confirmation email via SendGrid to {email}")
            else:
                logger.error(f"SendGrid confirmation email sending failed for {email}")
        
        # Fall back to SMTP if SendGrid failed or not available
        if not sent:
            if settings.GMAIL_USERNAME and settings.GMAIL_APP_PASSWORD:
                email_provider_available = True
                logger.info(f"Attempting to send confirmation email via SMTP to {email}")
                sent = await send_via_smtp(
                    email,
                    "Confirm Your LearnByEmail Account",
                    confirmation_url
                )
                
                if sent:
                    logger.info(f"Successfully sent confirmation email via SMTP to {email}")
                else:
                    logger.error(f"SMTP confirmation email sending failed for {email}")
                    
        if not email_provider_available:
            logger.error("No email provider credentials configured. Cannot send confirmation email.")
            
        return sent
    
    except Exception as e:
        logger.error(f"Error sending confirmation email: {type(e).__name__}: {str(e)}")
        return False


async def send_educational_email_task(subscription_id: int):
    """Send educational email to a subscriber"""
    db = SessionLocal()
    try:
        # Get subscription
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            logger.error(f"Subscription {subscription_id} not found")
            return False
            
        # Check if user's email is confirmed (for users with accounts)
        if subscription.user_id:
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user and user.email_confirmed != 1:
                logger.warning(f"Email not confirmed for user {user.id} (subscription {subscription_id}). Skipping email.")
                return False
        
        # Check if we already sent an email in the last hour
        now = datetime.utcnow()
        if subscription.last_sent and (now - subscription.last_sent).total_seconds() < 3600:
            logger.info(f"Skipping email for {subscription.email} - too soon since last send")
            return False
        
        # Get all previous content for enhanced continuity
        previous_history = db.query(EmailHistory).filter(
            EmailHistory.subscription_id == subscription.id
        ).order_by(EmailHistory.sent_at.asc()).all()
        
        # Extract content from history records
        previous_contents = [h.content for h in previous_history]
        
        # Get sequence number (for "Lesson X" labeling)
        sequence_number = len(previous_history) + 1
        
        logger.info(f"Generating content for subscription {subscription_id}, lesson #{sequence_number} with {len(previous_contents)} previous lessons as context")
        
        # Generate content with difficulty level
        difficulty = str(subscription.difficulty or "medium")  # Use 'medium' as fallback if None
        content = await generate_educational_content(
            topic=str(subscription.topic),
            previous_contents=[str(c) for c in previous_contents] if previous_contents else None,
            difficulty=difficulty
        )
        if not content:
            logger.error(f"Failed to generate content for {subscription.email}")
            return False
        
        # Format HTML content for email with lesson number
        topic_url_encoded = urllib.parse.quote(str(subscription.topic))
        
        # Create a plain text version of the content for ChatGPT by extracting just the title
        import re
        title_match = re.search(r'<h2[^>]*>(.*?)</h2>', content, re.DOTALL)
        content_title = title_match.group(1).strip() if title_match else subscription.topic
        
        # Use just the title for the ChatGPT prompt to avoid HTML tags
        chatgpt_prompt = f"I just learned about {subscription.topic}: {content_title}. Can you help me understand this better?"
        chatgpt_prompt_encoded = urllib.parse.quote(chatgpt_prompt)
        
        # Include lesson sequence number for continuity
        lesson_badge = f"""<div style="display: inline-block; background-color: #3498db; color: white; padding: 5px 10px; border-radius: 4px; font-size: 0.9em; margin-bottom: 15px;">Lesson #{sequence_number}</div>"""
        
        # Create registration CTA for users without accounts
        registration_cta = ""
        if not subscription.user_id:
            registration_cta = f"""
            <!-- Registration CTA for users without accounts -->
            <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-left: 4px solid #4285f4; border-radius: 4px;">
                <h3 style="color: #4285f4; margin-top: 0;">Manage Your Learning Experience</h3>
                <p>Want to manage your subscriptions, adjust delivery times, or subscribe to more topics?</p>
                <p><a href="{settings.BASE_URL}/register?email={subscription.email}" style="display: inline-block; background-color: #4285f4; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; font-weight: bold;">Create Your Free Account</a></p>
                <p style="font-size: 0.9em; color: #666;">With an account, you can easily manage all your educational subscriptions in one place.</p>
            </div>
            """
        
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto;">
            {lesson_badge}
            {content}
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <h3 style="color: #34495e;">Continue Your Learning Journey</h3>
                <p>This is lesson #{sequence_number} in your {subscription.topic} learning journey.</p>
                <p>Want to explore this topic further? <a href="https://chatgpt.com/?q={chatgpt_prompt_encoded}">Continue learning with an AI tutor</a></p>
            </div>
            
            {registration_cta}
        </div>
        """
        
        # Check which email provider is available
        email_provider_available = False
        
        # Try SendGrid first
        sent = False
        if SENDGRID_AVAILABLE and settings.SENDGRID_API_KEY:
            email_provider_available = True
            logger.info(f"Attempting to send email via SendGrid to {subscription.email}")
            sent = await send_via_sendgrid(
                subscription.email,
                f"Your {subscription.topic} Lesson #{sequence_number}",
                html_content
            )
            
            if sent:
                logger.info(f"Successfully sent email via SendGrid to {subscription.email}")
            else:
                logger.error(f"SendGrid email sending failed for {subscription.email}")
        
        # Fall back to SMTP if SendGrid failed or not available
        if not sent:
            if settings.GMAIL_USERNAME and settings.GMAIL_APP_PASSWORD:
                email_provider_available = True
                logger.info(f"Attempting to send email via SMTP to {subscription.email}")
                sent = await send_via_smtp(
                    subscription.email,
                    f"Your {subscription.topic} Lesson #{sequence_number}",
                    html_content
                )
                
                if sent:
                    logger.info(f"Successfully sent email via SMTP to {subscription.email}")
                else:
                    logger.error(f"SMTP email sending failed for {subscription.email}")
                    
        if not email_provider_available:
            logger.error("No email provider credentials configured. Cannot send emails.")
        
        if sent:
            # Save the email content to history
            history = EmailHistory(subscription_id=subscription.id, content=content)
            db.add(history)
            
            # Update the last sent time - needs explicit update for SQLAlchemy Column type
            db.query(Subscription).filter(Subscription.id == subscription.id).update(
                {"last_sent": datetime.utcnow()})
            db.commit()
            logger.info(f"Successfully sent email to {subscription.email}")
            return True
        else:
            logger.error(f"Failed to send email to {subscription.email}")
            return False
    
    except Exception as e:
        logger.error(f"Error in send_educational_email_task: {type(e).__name__}: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()