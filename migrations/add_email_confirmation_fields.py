import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database connection
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def run_migration():
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if email_confirmed column exists
        result = db.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = [row[1] for row in result]
        
        # Add email_confirmed column if it doesn't exist
        if 'email_confirmed' not in columns:
            print("Adding email_confirmed column...")
            db.execute(text("ALTER TABLE users ADD COLUMN email_confirmed INTEGER DEFAULT 1"))
            # Set all existing users as confirmed (1) to avoid disrupting their experience
            db.execute(text("UPDATE users SET email_confirmed = 1"))
            print("All existing users have been marked as confirmed.")
        else:
            print("email_confirmed column already exists.")
        
        # Add confirmation_token column if it doesn't exist
        if 'confirmation_token' not in columns:
            print("Adding confirmation_token column...")
            db.execute(text("ALTER TABLE users ADD COLUMN confirmation_token TEXT"))
        else:
            print("confirmation_token column already exists.")
        
        # Add confirmation_token_expires column if it doesn't exist
        if 'confirmation_token_expires' not in columns:
            print("Adding confirmation_token_expires column...")
            db.execute(text("ALTER TABLE users ADD COLUMN confirmation_token_expires TIMESTAMP"))
        else:
            print("confirmation_token_expires column already exists.")
        
        # Commit the changes
        db.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting migration to add email confirmation fields...")
    run_migration()
    print("Migration finished.")
