import logging
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import text
from app.db.session import engine, Base, SessionLocal
from app.db.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add email confirmation fields to User model and set existing users as confirmed"""
    logger.info("Running email confirmation migration...")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if columns already exist to avoid errors
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        # Add email_confirmed column if it doesn't exist
        if 'email_confirmed' not in columns:
            logger.info("Adding email_confirmed column to users table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN email_confirmed INTEGER DEFAULT 0 NOT NULL"))
                conn.commit()
        
        # Add confirmation_token column if it doesn't exist
        if 'confirmation_token' not in columns:
            logger.info("Adding confirmation_token column to users table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN confirmation_token VARCHAR(256)"))
                conn.commit()
        
        # Add confirmation_token_expires column if it doesn't exist
        if 'confirmation_token_expires' not in columns:
            logger.info("Adding confirmation_token_expires column to users table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN confirmation_token_expires DATETIME"))
                conn.commit()
        
        # Set existing users as confirmed (grandfather clause)
        logger.info("Setting existing users as confirmed")
        db.execute(text("UPDATE users SET email_confirmed = 1 WHERE email_confirmed IS NULL OR email_confirmed = 0"))
        db.commit()
        
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
