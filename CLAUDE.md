# LearnByEmail FastAPI Development Guide

## Commands
- Activate virtual environment first: `source learnbyemail-venv/bin/activate`
- Run app: `python3 main.py`
- Run with uvicorn: `uvicorn app.main:app --reload`
- View logs: `tail -f app.log`
- Test email sending: Use the dashboard "Test Send Email Now" button or `curl http://localhost:8000/test-email/{subscription_id}`
- Reset database: Delete `learnbyemail.db` and restart the app
- Manage database: `alembic revision --autogenerate -m "message"` and `alembic upgrade head` (if alembic is configured)

## Environment Variables
- `API_SECRET_KEY`: Required for app security and JWT (must be at least 32 chars, generate with `python -m app.core.security`)
- `DATABASE_URL`: SQLite or PostgreSQL connection string
- `BASE_URL`: Your application's public URL (e.g., "https://learnbyemail.com" or "http://yourdomain.com")
- `GEMINI_API_KEY`: For content generation with Google's Gemini API (supports all model versions)
- `SENDGRID_API_KEY`: For SendGrid email delivery
- `SENDGRID_FROM_EMAIL`: Sender address for SendGrid
- `SENDGRID_FROM_NAME`: Display name for sender (e.g., "LearnByEmail")

## Code Style
- Imports: Standard library → third-party → local modules
- Naming: snake_case for variables/functions, PascalCase for classes
- Security: Never log credentials or PII, sanitize all user inputs
- Error handling: Use specific exceptions, log error types and messages
- Database: Use SQLAlchemy ORM, avoid raw queries
- API: Follow RESTful design principles
- Templates: Extend base.html, use consistent block structure

## Security Best Practices
- CSRF: All forms should include CSRF token via {% include "_csrf_token.html" %}
- CSRF: All POST/PUT/DELETE API endpoints should use dependencies=[Depends(verify_csrf_token)]
- CSRF: AJAX requests must include 'X-CSRF-Token' header with token from form or cookie
- Rate Limiting: Apply strict_rate_limit() to auth endpoints: dependencies=[Depends(strict_rate_limit())]
- Rate Limiting: Apply standard_rate_limit() to general API endpoints: dependencies=[Depends(standard_rate_limit())]
- Admin: Use dependencies=[Depends(get_current_user)] and check is_admin property
- Tokens: All user-specific tokens should expire (password reset: 24h, session: 7d)
- Validation: Validate all user inputs with appropriate constraints
- Logging: Log security events but never log sensitive values (use masking)

## FastAPI Specifics
- Use dependency injection for database sessions, authentication
- Define Pydantic models in schemas directory
- Implement API routes in api directory
- Use proper HTTP status codes
- Document API endpoints with docstrings

## Troubleshooting
- Check `app.log` for detailed error messages
- Verify that your API keys are valid and not expired
- For email issues, check that sender address is verified in SendGrid
- For Gemini issues, check that your API key has access to the models
- Database issues: Check SQLite file permissions or connection string
- JWT issues: Ensure SECRET_KEY is properly set in .env
- Dependencies issues: Ensure you're using the correct virtual environment (learnbyemail-venv) and run `pip install -r requirements.txt` if missing packages