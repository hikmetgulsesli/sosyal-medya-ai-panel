"""Configuration settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    database_url: str = "postgresql://user:password@localhost:5432/db"
    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    secret_key: str = "secret-key-for-jwt"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
