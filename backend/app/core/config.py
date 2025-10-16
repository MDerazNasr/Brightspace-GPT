# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings with defaults."""
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8001"
    
    # Database - with defaults for development
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/uottawa_assistant"
    REDIS_URL: str = "redis://localhost:6379"
    LOG_SQL_QUERIES: bool = False  # ← ADD THIS LINE
    
    # Brightspace API
    BRIGHTSPACE_API_URL: str = "https://uottawa.brightspace.com/d2l/api"
    BRIGHTSPACE_API_VERSION: str = "1.0"
    
    # OAuth
    BRIGHTSPACE_OAUTH_CLIENT_ID: str = ""
    BRIGHTSPACE_OAUTH_CLIENT_SECRET: str = ""
    BRIGHTSPACE_OAUTH_REDIRECT_URI: str = "http://localhost:8001/api/auth/brightspace/callback"
    
    # LLM
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-large-latest"
    
    # Vector DB
    VECTOR_DB_URL: str = "http://localhost:6333"
    VECTOR_COLLECTION_NAME: str = "uottawa_courses"
    
    # Auth & Security
    JWT_SECRET: str = "dev_secret_key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "*"]
    
    # Development
    USE_MOCK_BRIGHTSPACE: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = "allow"  # Allow extra fields

settings = Settings()