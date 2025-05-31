import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, AnyHttpUrl, Field # Consolidated Field import

class Settings(BaseSettings):
    # General App Settings
    APP_NAME: str = "AutoBidder API"
    APP_DEBUG: bool = True
    
    # Database
    # Users should update this in their .env file for their specific PostgreSQL setup.
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/autobidderdb"

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

    # Captcha Service Configuration
    CAPTCHA_PROVIDER_NAME: str = Field(default="capmonster", env="CAPTCHA_PROVIDER_NAME") # "capmonster", "2captcha", "anticaptcha"

    # Provider-specific API Keys
    CAPMONSTER_API_KEY: Optional[str] = Field(default=None, env="CAPMONSTER_API_KEY")
    TWOCAPTCHA_API_KEY: Optional[str] = Field(default=None, env="TWOCAPTCHA_API_KEY")
    ANTICAPTCHA_API_KEY: Optional[str] = Field(default=None, env="ANTICAPTCHA_API_KEY")

    # CapMonster URLs (existing)
    CAPMONSTER_CREATE_TASK_URL: AnyHttpUrl = Field(default="https://api.capmonster.cloud/createTask", env="CAPMONSTER_CREATE_TASK_URL") # type: ignore
    CAPMONSTER_GET_TASK_URL: AnyHttpUrl = Field(default="https://api.capmonster.cloud/getTaskResult", env="CAPMONSTER_GET_TASK_URL") # type: ignore

    # 2Captcha URLs
    TWOCAPTCHA_CREATE_TASK_URL: AnyHttpUrl = Field(default="https://api.2captcha.com/createTask", env="TWOCAPTCHA_CREATE_TASK_URL") # type: ignore
    TWOCAPTCHA_GET_TASK_URL: AnyHttpUrl = Field(default="https://api.2captcha.com/getTaskResult", env="TWOCAPTCHA_GET_TASK_URL") # type: ignore

    # AntiCaptcha URLs
    ANTICAPTCHA_CREATE_TASK_URL: AnyHttpUrl = Field(default="https://api.anti-captcha.com/createTask", env="ANTICAPTCHA_CREATE_TASK_URL") # type: ignore
    ANTICAPTCHA_GET_TASK_URL: AnyHttpUrl = Field(default="https://api.anti-captcha.com/getTaskResult", env="ANTICAPTCHA_GET_TASK_URL") # type: ignore

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

    # ML Model Settings
    ML_PREDICTION_ENDPOINT_URL: AnyHttpUrl = "http://localhost:8000/ml/predict_success_proba" # type: ignore
    ML_PROBABILITY_THRESHOLD: float = 0.5
    MODEL_PATH: str = "app/ml_model/artifacts/model.joblib"
    # Note: The old CAPTCHA_API_KEY and CAPTCHA_PROVIDER fields are now replaced by
    # CAPTCHA_PROVIDER_NAME and provider-specific API key fields.

    # Upwork Credentials for automated login (optional)
    UPWORK_USERNAME: Optional[str] = Field(default=None, env="UPWORK_USERNAME")
    UPWORK_PASSWORD: Optional[str] = Field(default=None, env="UPWORK_PASSWORD")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
