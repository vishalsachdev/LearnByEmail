from typing import List, Optional
import os
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "LearningPulse"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "default-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./learningpulse.db")
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[AnyHttpUrl]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Email settings
    GMAIL_USERNAME: Optional[str] = os.getenv("GMAIL_USERNAME")
    GMAIL_APP_PASSWORD: Optional[str] = os.getenv("GMAIL_APP_PASSWORD")
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL: Optional[str] = os.getenv("SENDGRID_FROM_EMAIL", "noreply@learningpulse.app")
    
    # Content generation
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()