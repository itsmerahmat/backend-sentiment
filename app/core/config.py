import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App settings
    APP_NAME: str = "Sentiment API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./database.db"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    
    # Apify settings
    APIFY_TOKEN: str = ""
    APIFY_INSTAGRAM_PROFILE_SCRAPER_ID: str = ""
    APIFY_INSTAGRAM_POST_SCRAPER_ID: str = ""
    APIFY_INSTAGRAM_COMMENTS_SCRAPER_ID: str = ""
    
    # IndoBERT model settings
    INDOBERT_MODEL_DIR: str = "app/sentiment/indobert_model"
    
    # Lexicon settings
    LEXICON_DIR: str = "app/sentiment/lexicon_based"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
