from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/fintech_app"
    
    # Plaid API
    plaid_client_id: str
    plaid_secret: str
    plaid_env: str = "sandbox"  # sandbox, development, production
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # AI Analysis
    openai_api_key: Optional[str] = None
    
    # Application
    app_name: str = "Financial Transaction Aggregator"
    debug: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()