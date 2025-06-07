from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Onshape API Credentials
    onshape_access_key: str
    onshape_secret_key: str
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # # Security
    # secret_key: str = "your-secret-key-here"
    # algorithm: str = "HS256"
    # access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 