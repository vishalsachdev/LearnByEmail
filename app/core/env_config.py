import os
import sys
from dotenv import load_dotenv

def load_environment_variables():
    """
    Load environment variables from the appropriate source
    based on the current environment (Replit or local).
    """
    # Check if running on Replit (REPL_ID exists in Replit environment)
    is_replit = 'REPL_ID' in os.environ
    
    # On local environment, load from .env file
    if not is_replit:
        load_dotenv()
        print("Local environment detected: Loading from .env file")
    else:
        print("Replit environment detected: Using Replit Secrets")
    
    # Validate critical environment variables
    required_vars = ['API_SECRET_KEY', 'SENDGRID_API_KEY', 'GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"WARNING: Missing required environment variables: {', '.join(missing_vars)}")
        if is_replit:
            print("Please add these missing variables to Replit Secrets")
        else:
            print("Please add these missing variables to your .env file")
    
    return is_replit