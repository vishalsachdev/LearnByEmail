# LearnByEmail FastAPI - Comprehensive Documentation

## Overview

LearnByEmail is an educational content delivery platform that sends personalized, AI-generated educational emails on topics of the user's choice. This implementation uses FastAPI for improved performance, Gemini AI for content generation, and SendGrid/SMTP for email delivery. The modern, responsive UI provides an intuitive user experience across all devices.

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
- Test email functionality
- Background task processing for non-blocking operation

### Scheduling

- APScheduler for scheduled email delivery
- Timezone-aware scheduling
- Subscription-based delivery times

### User Interface

- Modern, responsive design across all devices
- Consistent color scheme and visual language
- Intuitive navigation and user flows
- Interactive form elements with validation
- Direct subscription form on the landing page
- Dashboard with subscription management
- Clean, card-based layout for better organization
- Visual feedback for user actions
- Content preview feature with difficulty selection
- Mobile-optimized layouts with touch-friendly controls
- Automatic timezone detection from browser settings
- Accessibility considerations for all users

## Environment Configuration

Create a `.env` file in the root directory with the following variables:

```
# Required settings - SECURITY CRITICAL
# Generate a secure key with: python -m app.core.security
API_SECRET_KEY=your-secure-generated-key-minimum-32-characters-long
DATABASE_URL=sqlite:///./learnbyemail.db

# Content generation (required)
GEMINI_API_KEY=your-gemini-api-key

# Email sending (choose one method)
# Option 1: SendGrid (recommended)
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=your-verified-sender@example.com

# Option 2: Gmail SMTP
GMAIL_USERNAME=your-gmail-username@gmail.com
GMAIL_APP_PASSWORD=your-app-specific-password
```

> **Note**: For email delivery to work, you must configure either SendGrid (recommended) or Gmail SMTP. Without these settings, the application will generate content but won't be able to deliver emails.

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

### Content Preview

- `POST /api/v1/preview/generate`: Generate a content preview for a topic
  - Parameters: `topic` (required), `difficulty` (optional: easy, medium, hard)

### Web UI Routes

- `GET /`: Home page
- `GET /login`: Login page
- `POST /login`: Process login
- `GET /register`: Registration page
- `POST /register`: Process registration
- `GET /dashboard`: User dashboard
- `POST /subscribe`: Create subscription from form
- `GET /test-email/{id}`: Test send an email immediately
- `GET /check-env`: Display current environment configuration (debugging)
- `GET /direct-test-email/{email}`: Send a direct test email (debugging)

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

### Frontend Assets

- Static assets are served directly from FastAPI
- CSS is primarily embedded for faster page loads in this version
- Consider using a CDN for static assets in high-traffic production environments
- Maintain the color scheme defined in CSS variables for consistency

## UI/UX Design

### Design Principles

- **Consistency**: Consistent color scheme, typography, and spacing across all pages
- **Responsiveness**: Mobile-first design that adapts to all screen sizes
- **Accessibility**: High-contrast text, clear navigation, and proper form labels
- **User Feedback**: Visual feedback for user actions and form validation
- **Simplicity**: Clean, uncluttered layouts that focus on the content

### Color Scheme

- Primary color: #34a853 (green)
- Secondary color: #4285f4 (blue)
- Accent color: #ea4335 (red)
- Background color: #f8f9fa (light gray)
- Text colors: #333 (dark gray), #666 (medium gray)

### Key Templates

- `simple.html`: Landing page with feature showcase and subscription form
- `simple_login.html`: User login page
- `simple_register.html`: User registration with benefits list
- `simple_dashboard.html`: User dashboard with subscription management
- `base.html`: Template base with common styles for other templates

## Troubleshooting

### Common Issues

1. **Email Delivery Failing**
   - Check SendGrid API key validity
   - Verify sender email is authorized in SendGrid
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

5. **UI Display Issues**
   - Clear browser cache if styles aren't updating
   - Check browser console for JavaScript errors
   - Verify that all required static assets are being served correctly
   - Test on different browsers and devices for compatibility issues