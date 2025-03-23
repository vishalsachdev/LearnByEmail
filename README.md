# LearnByEmail

![LearnByEmail Banner](https://github.com/vishalsachdev/LearnByEmail/assets/banner.png)

LearnByEmail is an educational email subscription service that delivers personalized, AI-generated educational content on topics of your choice. The service is designed to help students learn new subjects through daily bite-sized lessons delivered directly to your inbox at your preferred time.

## 📚 How It Works

1. **Choose a topic** you want to learn about (Python, History, Physics, Art, etc.)
2. **Select your difficulty level** (Beginner, Intermediate, Advanced)
3. **Set your preferred delivery time** and timezone
4. **Receive daily educational emails** with bite-sized lessons on your chosen topic

![Dashboard Screenshot](https://github.com/vishalsachdev/LearnByEmail/assets/dashboard.png)

## Features

- User registration and authentication with JWT
- Email confirmation system for new registrations
- Topic-based educational content subscriptions
- AI-generated content using Google's Gemini models (automatically selects best available model)
- Scheduled email delivery at preferred times
- Email delivery via Gmail SMTP or SendGrid
- Dashboard for managing subscriptions

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Jinja2**: Template engine for HTML rendering
- **APScheduler**: Advanced Python scheduler for email jobs
- **Google Generative AI**: For creating educational content with dynamic model selection
- **SendGrid/SMTP**: For email delivery
- **Pydantic**: Data validation and settings management

## Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourfork/LearnByEmail.git
   cd LearnByEmail
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv learnbyemail-venv
   source learnbyemail-venv/bin/activate  # On Windows: learnbyemail-venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file with the following):
   ```
   # Required settings - SECURITY CRITICAL
   # Generate a secure key with: python -m app.core.security
   API_SECRET_KEY=your-secure-generated-key-minimum-32-characters-long
   
   # Your application's public URL (used for password reset emails, etc.)
   BASE_URL=http://localhost:8000
   
   # Content generation (required)
   GEMINI_API_KEY=your-gemini-api-key
   
   # Email sending (choose one method)
   # Option 1: SendGrid
   SENDGRID_API_KEY=your-sendgrid-api-key
   SENDGRID_FROM_EMAIL=your-verified-sender@example.com
   SENDGRID_FROM_NAME=LearnByEmail
   
   # Option 2: Gmail SMTP
   GMAIL_USERNAME=your-gmail-username
   GMAIL_APP_PASSWORD=your-gmail-app-password
   ```

### Replit Deployment

To deploy the application on Replit:

1. Create a new Replit from this repository
2. Add the following Secrets in the Replit environment:
   - `API_SECRET_KEY`: Secure random key (minimum 32 characters)
   - `BASE_URL`: Your public URL (e.g., https://learnbyemail.com or your Replit URL)
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `SENDGRID_API_KEY`: Your SendGrid API key
   - `SENDGRID_FROM_EMAIL`: Your verified sender email
   - `SENDGRID_FROM_NAME`: Display name for sender (e.g., "LearnByEmail")

3. The application will automatically detect the Replit environment and use these secrets instead of a .env file.

4. Run the application using the Replit Run button or `python main.py`

## Running the Application

Run the application with:

```bash
python main.py
```

Or directly with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The application will be available at http://localhost:8000.

### Testing Email Sending

After registering and creating a subscription, you can test email sending immediately:

1. Go to your dashboard at http://localhost:8000/dashboard
2. Click the "Test Send Email Now" button next to your subscription
3. The application will attempt to generate content and send an email
4. Check the logs for detailed information (./app.log)

## API Documentation

FastAPI automatically generates interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Project Structure

- `app/`: Main application package
  - `api/`: API endpoints
  - `core/`: Core functionality (config, security)
  - `db/`: Database models and session management
  - `schemas/`: Pydantic models for data validation
  - `services/`: Business logic services
    - `content_generator.py`: AI content generation with Gemini
    - `email_sender.py`: Email delivery via SendGrid or SMTP
    - `scheduler.py`: Scheduled email delivery
  - `templates/`: Jinja2 HTML templates
  - `main.py`: FastAPI application instance
  - `static/`: Static assets (JS, CSS, images)

### Running Tests

To run tests:

```bash
pytest
```

## 🤝 Contributing

We welcome feedback, suggestions, and bug reports from students and educators! This project is designed to help you learn, and your input helps make it better.

- **Found a bug?** Open an issue describing what happened and what you expected
- **Have a feature idea?** Share your thoughts through the issues section
- **Need help?** Ask questions in the discussions area

See our [CONTRIBUTING.md](CONTRIBUTING.md) for more details on how to get involved.

## 📣 Community

Join our growing community of learners:

- [GitHub Discussions](https://github.com/vishalsachdev/LearnByEmail/discussions) - Ask questions and share ideas
- For private inquiries, visit our [Contact Page](https://learnbyemail.com/contact)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.