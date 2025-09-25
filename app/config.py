from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./financial_app.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Plaid Configuration
    plaid_client_id: str = ""
    plaid_secret: str = ""
    plaid_env: str = "sandbox"  # sandbox, development, production
    plaid_products: str = "transactions,accounts,identity"
    
    # App Configuration
    app_name: str = "Financial Data Aggregator"
    debug: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()