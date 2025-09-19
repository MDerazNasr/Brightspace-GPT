from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: list = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
