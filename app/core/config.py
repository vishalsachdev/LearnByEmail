from typing import List, Optional, Union, Any
import os
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from app.core.env_config import load_environment_variables

# Load environment variables from the appropriate source
is_replit = load_environment_variables()


class Settings(BaseSettings):
    PROJECT_NAME: str = "LearnByEmail"
    API_V1_STR: str = "/api/v1"
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    @property
    def SECRET_KEY(self) -> str:
        """Use API_SECRET_KEY for the application's secret key."""
        if not self.API_SECRET_KEY:
            raise ValueError("API_SECRET_KEY environment variable is required for security")
        if self.API_SECRET_KEY == "default-secret-key-change-in-production":
            raise ValueError("Default API_SECRET_KEY detected. Please change it for security")
        if len(self.API_SECRET_KEY) < 32:
            raise ValueError("API_SECRET_KEY must be at least 32 characters long")
        return self.API_SECRET_KEY
        
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Cookie security settings
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")  # 'lax', 'strict', or 'none'
    
    @property
    def COOKIE_SECURE(self) -> bool:
        """
        Determine if cookies should be secure based on BASE_URL.
        
        If BASE_URL starts with https://, set secure=True for production/https environments.
        This prevents cookies from being sent over non-HTTPS connections.
        """
        return self.BASE_URL.startswith("https://")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./learnbyemail.db")
    
    # GitHub Webhook
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[AnyHttpUrl]:
        if isinstance(v, str) and not v.startswith("["):
            return [AnyHttpUrl(i.strip()) for i in v.split(",")]
        elif isinstance(v, list):
            return [AnyHttpUrl(i) for i in v]
        elif isinstance(v, str):
            return [AnyHttpUrl(v)]
        raise ValueError(v)
    
    # Email settings
    GMAIL_USERNAME: Optional[str] = os.getenv("GMAIL_USERNAME")
    GMAIL_APP_PASSWORD: Optional[str] = os.getenv("GMAIL_APP_PASSWORD")
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL: Optional[str] = os.getenv("SENDGRID_FROM_EMAIL", "learning@learnbyemail.com")
    SENDGRID_FROM_NAME: Optional[str] = os.getenv("SENDGRID_FROM_NAME", "LearnByEmail")
    
    # Content generation
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    class Config:
        case_sensitive = True
        env_file = ".env" if not is_replit else None
        extra = "allow"


settings = Settings()