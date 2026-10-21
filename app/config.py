"""
Loads settings from the .env file so nothing is hardcoded.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str 
    anthropic_api_key: str = ""
    upload_dir: str = "uploads"
    extraction_model: str = "claude-sonnet-5-5"

    class Config:
        env_file = ".env"


settings = Settings()