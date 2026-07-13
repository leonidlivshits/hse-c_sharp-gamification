"""
app/core/config.py
DESCRIPTION: application configuration via pydantic BaseSettings.
- Reads individual DB components from env (POSTGRES_*) and constructs an async URL:
  postgresql+asyncpg://<user>:<pass>@<host>:<port>/<db>
- If DATABASE_URL is provided explicitly in env, it will be used as-is.
TODO: In production use secrets manager and do not commit secrets to VCS.
"""
from ipaddress import IPv4Network, IPv6Network, ip_network

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # app
    app_env: str = Field("development")
    app_host: str = Field("0.0.0.0")
    app_port: int = Field(8000)
    secret_key: str = Field("replace-me-please-change")
    jwt_secret_key: str | None = None
    admin_session_secret_key: str | None = None

    # DB - either DATABASE_URL or components
    database_url: str | None = None

    postgres_user: str = Field("postgres")
    postgres_password: str = Field("postgres")
    postgres_db: str = Field("app_db")
    postgres_host: str = Field("postgres")
    postgres_port: int = Field(5432)
    db_pool_size: int = Field(10)
    db_max_overflow: int = Field(20)
    db_pool_timeout_seconds: int = Field(30)
    db_pool_recycle_seconds: int = Field(1800)
    db_pool_pre_ping: bool = Field(True)

    # secret / auth
    algorithm: str = Field("HS256")
    access_token_expire_minutes: int = Field(60 * 24)
    db_auto_create: bool = Field(False)

    # OAuth2 settings (token url used by OAuth2PasswordBearer)
    oauth2_token_url: str = Field("/api/v1/auth/token")

    # password hashing schemes (comma-separated in env, default bcrypt)
    hash_schemes: str = Field("bcrypt")
    password_policy_min_length: int = Field(10)
    password_policy_require_uppercase: bool = Field(True)
    password_policy_require_lowercase: bool = Field(True)
    password_policy_require_digit: bool = Field(True)
    password_policy_require_special: bool = Field(True)
    password_policy_disallow_whitespace: bool = Field(True)

    # Redis
    redis_url: str = Field("redis://redis:6379/0")
    redis_port: int = Field(6379)

    # Background tasks
    background_tasks_backend: str = Field("redis")  # redis | celery
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_task_soft_time_limit_seconds: int = Field(120)
    celery_task_time_limit_seconds: int = Field(180)
    celery_task_max_retries: int = Field(5)
    celery_worker_concurrency: int = Field(4)

    # CORS
    cors_allow_origins: str = Field(
        "http://localhost:3002,http://127.0.0.1:3002,http://localhost:8080,http://127.0.0.1:8080",
    )
    cors_allow_credentials: bool = Field(True)

    # Rate limiting
    rate_limit_enabled: bool = Field(True)
    rate_limit_window_seconds: int = Field(60)
    rate_limit_default: int = Field(300)
    rate_limit_auth: int = Field(20)
    rate_limit_tests_read: int = Field(1200)
    rate_limit_answers_read: int = Field(900)
    rate_limit_answers: int = Field(180)
    rate_limit_analytics: int = Field(120)
    rate_limit_learning_dashboard: int = Field(300)
    rate_limit_ai: int = Field(30)
    rate_limit_password: int = Field(10)
    rate_limit_admin: int = Field(120)
    rate_limit_admin_login: int = Field(10)

    # Monitoring / observability
    monitoring_enabled: bool = Field(True)
    monitoring_metrics_token: str | None = None

    # Admin panel
    admin_enabled: bool = Field(True)
    admin_base_url: str = Field("/admin")
    admin_session_max_age_seconds: int = Field(60 * 60 * 8)
    admin_session_https_only: bool = Field(False)
    admin_session_same_site: str = Field("lax")
    admin_allowed_ips: str = Field("")
    admin_login_max_attempts: int = Field(5)
    admin_login_window_seconds: int = Field(300)
    admin_login_block_seconds: int = Field(900)
    admin_mfa_enabled: bool = Field(False)
    admin_mfa_totp_secret: str | None = None
    admin_mfa_totp_period_seconds: int = Field(30)
    admin_mfa_totp_digits: int = Field(6)
    admin_mfa_totp_drift_windows: int = Field(1)

    # AI / OpenRouter
    ai_gamification_enabled: bool = Field(False)
    ai_gamification_daily_quota_per_user: int = Field(20)
    ai_gamification_max_source_chars: int = Field(12000)
    ai_gamification_job_max_retries: int = Field(2)
    openrouter_api_key: str | None = None
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1")
    openrouter_model: str = Field("openrouter/auto")
    openrouter_fallback_models: str = Field("")
    openrouter_timeout_seconds: int = Field(30)
    openrouter_max_retries: int = Field(2)
    openrouter_site_url: str | None = None
    openrouter_app_name: str = Field("hse-c-sharp-gamification")

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

    def get_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    def get_openrouter_fallback_models(self) -> list[str]:
        models = [m.strip() for m in self.openrouter_fallback_models.split(",") if m.strip()]
        return models

    def get_jwt_secret_key(self) -> str:
        return (self.jwt_secret_key or self.secret_key).strip()

    def get_admin_session_secret_key(self) -> str:
        return (self.admin_session_secret_key or self.secret_key).strip()

    def get_monitoring_metrics_token(self) -> str:
        return (self.monitoring_metrics_token or "").strip()

    def get_background_tasks_backend(self) -> str:
        value = (self.background_tasks_backend or "redis").strip().lower()
        return value if value in {"redis", "celery"} else "redis"

    def get_celery_broker_url(self) -> str:
        return (self.celery_broker_url or self.redis_url).strip()

    def get_celery_result_backend(self) -> str:
        return (self.celery_result_backend or self.redis_url).strip()

    def get_admin_session_same_site(self) -> str:
        if self.app_env.lower() == "production":
            return "strict"
        value = (self.admin_session_same_site or "").strip().lower()
        if value in {"lax", "strict", "none"}:
            return value
        return "lax"

    def get_admin_allowed_ips(self) -> set[str]:
        return {ip.strip() for ip in self.admin_allowed_ips.split(",") if ip.strip()}

    def get_admin_allowed_networks(self) -> tuple[IPv4Network | IPv6Network, ...]:
        networks = []
        for raw_value in self.admin_allowed_ips.split(","):
            candidate = raw_value.strip()
            if not candidate:
                continue
            if "/" not in candidate:
                suffix = "/128" if ":" in candidate else "/32"
                candidate = f"{candidate}{suffix}"
            networks.append(ip_network(candidate, strict=False))
        return tuple(networks)


settings = Settings()
