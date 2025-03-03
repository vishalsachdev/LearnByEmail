# LearningPulse FastAPI - Comprehensive Documentation

## Overview

LearningPulse is an educational content delivery platform that sends personalized, AI-generated educational emails on topics of the user's choice. This implementation uses FastAPI for improved performance, Gemini AI for content generation, and SendGrid/SMTP for email delivery.

## Architecture

The application follows a modular architecture with clean separation of concerns:

```
app/
├── api/                  # API endpoints
│   ├── auth.py           # Authentication routes
│   └── subscriptions.py  # Subscription management
├── core/                 # Core configuration
│   ├── config.py         # Settings and environment variables
│   └── security.py       # JWT authentication, password hashing
├── db/                   # Database access
│   ├── models.py         # SQLAlchemy ORM models
│   └── session.py        # Database session management
├── schemas/              # Data validation
│   ├── subscription.py   # Subscription data schemas
│   └── user.py           # User data schemas
├── services/             # Business logic
│   ├── content_generator.py  # AI content generation
│   ├── email_sender.py       # Email delivery
│   └── scheduler.py          # Scheduled tasks
├── templates/            # HTML templates
└── static/               # Static assets
```

## Key Features

### User Authentication

- JWT-based authentication
- Password hashing with bcrypt
- Cookie-based token storage
- Optional user authentication for public routes

### Content Generation

- Uses Google's Gemini AI models
- Automatic model selection and fallback
- Content is structured for educational purposes
- Previous content is considered for continuity

### Email Delivery

- Primary: SendGrid API integration
- Fallback: SMTP via Gmail
- HTML-formatted educational emails
- Email history tracking

### Scheduling

- APScheduler for scheduled email delivery
- Timezone-aware scheduling
- Subscription-based delivery times

## Environment Configuration

Create a `.env` file in the root directory with the following variables:

```
# Required settings
FLASK_SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./learningpulse.db

# Content generation (required)
GEMINI_API_KEY=your-gemini-api-key

# Email sending (choose one method)
# Option 1: SendGrid
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=your-verified-sender@example.com

# Option 2: Gmail SMTP
GMAIL_USERNAME=your-gmail-username
GMAIL_APP_PASSWORD=your-gmail-app-password
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/login`: Authenticate and get JWT token
- `POST /api/v1/auth/register`: Register a new user
- `GET /api/v1/auth/me`: Get current user information

### Subscriptions

- `GET /api/v1/subscriptions/`: List user's subscriptions
- `POST /api/v1/subscriptions/`: Create a new subscription
- `GET /api/v1/subscriptions/{id}`: Get a specific subscription
- `PUT /api/v1/subscriptions/{id}`: Update a subscription
- `DELETE /api/v1/subscriptions/{id}`: Delete a subscription
- `GET /api/v1/subscriptions/{id}/history`: Get email history

### Web UI Routes

- `GET /`: Home page
- `GET /login`: Login page
- `POST /login`: Process login
- `GET /register`: Registration page
- `POST /register`: Process registration
- `GET /dashboard`: User dashboard
- `POST /subscribe`: Create subscription from form
- `GET /test-email/{id}`: Test send an email immediately

## Database Schema

### Users

- `id`: Integer primary key
- `email`: String, unique
- `password_hash`: String
- `created_at`: DateTime

### Subscriptions

- `id`: Integer primary key
- `email`: String
- `topic`: String
- `preferred_time`: Time
- `timezone`: String
- `created_at`: DateTime
- `last_sent`: DateTime (nullable)
- `user_id`: Integer foreign key

### EmailHistory

- `id`: Integer primary key
- `subscription_id`: Integer foreign key
- `content`: Text
- `sent_at`: DateTime

## Advanced Usage

### Testing Email Delivery

Use the test endpoint to send an email immediately:

```
GET /test-email/{subscription_id}
```

Or click the "Test Send Email Now" button on the dashboard.

### Logging

All logs are written to `app.log` in the root directory. View them with:

```bash
tail -f app.log
```

The logging level is set to DEBUG to provide detailed information for troubleshooting.

### Content Generation

The application will automatically try several Gemini models in this order:
1. gemini-2.0-flash
2. gemini-1.5-flash
3. gemini-1.5-pro
4. gemini-pro

The content generator will use the first available model that works with your API key.

## Deployment Considerations

### Security

- Change the SECRET_KEY for production
- Use HTTPS in production
- Consider adding rate limiting
- Implement CSRF protection for production

### Database

- For production, use PostgreSQL or MySQL
- Set up database migrations with Alembic
- Consider connection pooling for high traffic

### Email Delivery

- For production, use SendGrid or other enterprise email service
- Verify your sender domain with SendGrid
- Implement email bounce handling
- Monitor delivery rates

### Scaling

- Deploy behind a reverse proxy (Nginx, Traefik)
- Consider containerization with Docker
- For high volumes, separate the scheduler into a dedicated worker
- Use a production ASGI server like Uvicorn behind Gunicorn

## Troubleshooting

### Common Issues

1. **Email Delivery Failing**
   - Check SendGrid API key validity
   - Verify sender email is authorized in SendGrid
   - Check SMTP credentials if using Gmail
   - Look for rate limiting or account restrictions

2. **Content Generation Errors**
   - Verify Gemini API key is valid
   - Check for quota limits on your API key
   - Review logs for specific error messages
   - Ensure internet connectivity for API calls

3. **Authentication Issues**
   - Check that SECRET_KEY is set
   - Clear browser cookies if experiencing login loops
   - Ensure password meets minimum requirements
   - Check for database connectivity issues

4. **Scheduling Problems**
   - Verify timezone settings
   - Check that APScheduler is running
   - Ensure database has correct time values
   - Check logs for scheduler exceptions