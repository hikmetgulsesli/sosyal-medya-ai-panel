from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/social_media_ai"
    
    # JWT
    jwt_secret: str = "your-super-secret-key-change-this-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3522"
    
    # Environment
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
