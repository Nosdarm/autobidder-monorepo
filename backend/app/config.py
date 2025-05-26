import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, AnyHttpUrl

class Settings(BaseSettings):
    # General App Settings
    APP_NAME: str = "AutoBidder API"
    APP_DEBUG: bool = True
    
    # Database
    # Users should update this in their .env file for their specific PostgreSQL setup.
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/autobidder_db"

    # JWT Authentication
    SECRET_KEY: str # No default, must be set in environment
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
    # For .env: CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000"

    # OpenAI Service
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_TIMEOUT: float = 15.0
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Captcha Service
    CAPTCHA_API_KEY: Optional[str] = None
    CAPTCHA_PROVIDER: str = "2captcha"
    CAPMONSTER_CREATE_TASK_URL: AnyHttpUrl = "https://api.capmonster.cloud/createTask" # type: ignore
    CAPMONSTER_GET_TASK_URL: AnyHttpUrl = "https://api.capmonster.cloud/getTaskResult" # type: ignore

    # Email Service (Mailtrap example)
    MAILTRAP_HOST: Optional[str] = None
    MAILTRAP_PORT: int = 2525
    MAILTRAP_USER: Optional[str] = None
    MAILTRAP_PASS: Optional[str] = None
    MAILTRAP_FROM: EmailStr = "AutoBidder <noreply@example.com>" # type: ignore
    EMAIL_VERIFICATION_HOST: str = "http://localhost:8000"

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None # If your Redis is password-protected
    REDIS_CACHE_TTL_SECONDS: int = 60 * 60  # Default TTL for cache (1 hour)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
