"""
app/core/config.py
DESCRIPTION: application configuration via pydantic BaseSettings.
- Reads individual DB components from env (POSTGRES_*) and constructs an async URL:
  postgresql+asyncpg://<user>:<pass>@<host>:<port>/<db>
- If DATABASE_URL is provided explicitly in env, it will be used as-is.
TODO: In production use secrets manager and do not commit secrets to VCS.
"""
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # app
    app_env: str = Field("development", env="APP_ENV")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    secret_key: str = Field("replace-me", env="SECRET_KEY")

    # DB - either DATABASE_URL or components
    database_url: Optional[str] = Field(None, env="DATABASE_URL")

    postgres_user: str = Field("postgres", env="POSTGRES_USER")
    postgres_password: str = Field("postgres", env="POSTGRES_PASSWORD")
    postgres_db: str = Field("app_db", env="POSTGRES_DB")
    postgres_host: str = Field("postgres", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")

    # Redis
    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_database_url(self) -> str:
        """
        Return the async SQLAlchemy URL to be used by the app.
        If DATABASE_URL provided explicitly, return it.
        Otherwise build from POSTGRES_* components.
        """
        if self.database_url:
            return self.database_url
        # assemble using asyncpg driver
        user = self.postgres_user
        pw = self.postgres_password
        host = self.postgres_host
        port = self.postgres_port
        db = self.postgres_db
        return f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{db}"


settings = Settings()
