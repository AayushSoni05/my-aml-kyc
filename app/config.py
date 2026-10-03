"""
Loads settings from the .env file so nothing is hardcoded.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./sentinel.db"

    class Config:
        env_file = ".env"


settings = Settings()