"""
app/core/config.py
DESCRIPTION: application configuration via pydantic BaseSettings.
TODO: In production, prefer a secrets manager and not .env files.
"""
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = Field("development", env="APP_ENV")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    secret_key: str = Field("replace-me", env="SECRET_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()