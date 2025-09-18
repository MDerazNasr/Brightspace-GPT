"""
Configuration management for the uOttawa Brightspace Assistant.
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/uottawa_assistant"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Brightspace API
    BRIGHTSPACE_API_URL: str = "https://uottawa.brightspace.com/d2l/api"
    BRIGHTSPACE_CLIENT_ID: str = ""
    BRIGHTSPACE_CLIENT_SECRET: str = ""
    BRIGHTSPACE_API_VERSION: str = "1.0"
    
    # LLM Configuration
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-large-latest"
    
    # Vector Database
    VECTOR_DB_URL: str = "http://localhost:6333"
    VECTOR_COLLECTION_NAME: str = "uottawa_courses"
    
    # Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # uOttawa SSO
    UNIVERSITY_SSO_URL: str = "https://sso.uottawa.ca"
    SSO_CLIENT_ID: str = ""
    SSO_CLIENT_SECRET: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://assistant.uottawa.ca"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Data Sync
    SYNC_INTERVAL_HOURS: int = 6
    MAX_SYNC_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
