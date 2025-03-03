import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
import urllib.parse
import asyncio

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Subscription, EmailHistory
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
        logger.info(f"SendGrid API key is set (length: {len(sendgrid_key)})")
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


async def create_html_email(subject, content, to_email):
    """Create HTML email message"""
    from_email, _ = await check_email_credentials()
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['Subject'] = subject
    msg['To'] = to_email

    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ font-size: 24px; margin-bottom: 20px; }}
            h2 {{ font-size: 20px; margin-top: 25px; }}
            p {{ margin: 15px 0; }}
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

        from_email = settings.SENDGRID_FROM_EMAIL
        logger.info(f"Attempting to send email via SendGrid from {from_email} to {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"SendGrid API Key length: {len(sendgrid_key) if sendgrid_key else 0}")
        
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        sg = SendGridAPIClient(sendgrid_key)
        logger.info("Initialized SendGrid client, sending message...")
        
        try:
            response = await asyncio.to_thread(sg.send, message)
            
            status_code = response.status_code
            logger.info(f"SendGrid Response: Status {status_code}")
            
            if status_code >= 200 and status_code < 300:
                logger.info("Email sent successfully via SendGrid")
                return True
            else:
                logger.error(f"SendGrid API error: {status_code}")
                logger.error(f"Response body: {response.body}")
                return False
        except Exception as send_error:
            logger.error(f"SendGrid send error: {type(send_error).__name__}: {str(send_error)}")
            if hasattr(send_error, 'body'):
                logger.error(f"SendGrid error body: {send_error.body}")
            return False

    except Exception as e:
        logger.error(f"SendGrid Error: {type(e).__name__}: {str(e)}")
        logger.error(f"SendGrid configuration: API KEY length={len(settings.SENDGRID_API_KEY) if settings.SENDGRID_API_KEY else 0}, FROM_EMAIL={settings.SENDGRID_FROM_EMAIL}")
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
            server.login(username, password)
            server.send_message(msg)
            
        logger.info(f"Successfully sent email via SMTP to {to_email}")
        return True
    except Exception as e:
        logger.error(f"SMTP Error: {type(e).__name__}: {str(e)}")
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
        
        # Check if we already sent an email in the last hour
        now = datetime.utcnow()
        if subscription.last_sent and (now - subscription.last_sent).total_seconds() < 3600:
            logger.info(f"Skipping email for {subscription.email} - too soon since last send")
            return False
        
        # Get previous content
        previous_contents = [
            h.content for h in db.query(EmailHistory).filter(
                EmailHistory.subscription_id == subscription.id
            ).order_by(EmailHistory.sent_at.desc()).limit(3).all()
        ]
        
        # Generate content
        content = await generate_educational_content(subscription.topic, previous_contents)
        if not content:
            logger.error(f"Failed to generate content for {subscription.email}")
            return False
        
        # Format HTML content for email
        topic_url_encoded = urllib.parse.quote(subscription.topic)
        content_preview = urllib.parse.quote(content[:100])
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto;">
            {content}
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <h3 style="color: #34495e;">Continue Learning</h3>
                <p>Want to explore this topic further? <a href="https://chat.openai.com/chat?prompt=Teach%20me%20more%20about%20{topic_url_encoded}%20building%20upon%20this%20lesson:%20{content_preview}">Discuss this lesson with an AI tutor</a></p>
            </div>
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
                f"Your Daily {subscription.topic} Lesson",
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
                    f"Your Daily {subscription.topic} Lesson",
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
            
            subscription.last_sent = datetime.utcnow()
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