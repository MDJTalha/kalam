from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_env: str = "development"
    app_name: str = Field(default="Corporate LMS API", alias="APP_NAME")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    web_origin: str = Field(default="http://localhost:3000", alias="WEB_ORIGIN")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", alias="ALLOWED_HOSTS")
    api_origin: str = Field(default="http://localhost:8000", alias="API_ORIGIN")
    session_cookie_name: str = Field(default="corp_lms_session", alias="SESSION_COOKIE_NAME")
    session_ttl_seconds: int = Field(default=28800, alias="SESSION_TTL_SECONDS")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_starttls: bool = Field(default=True, alias="SMTP_STARTTLS")
    dev_email_sink: bool = Field(default=True, alias="DEV_EMAIL_SINK")
    reset_token_minutes: int = Field(default=30, alias="RESET_TOKEN_MINUTES")
    max_failed_login_attempts: int = Field(default=5, alias="MAX_FAILED_LOGIN_ATTEMPTS")
    login_lockout_minutes: int = Field(default=15, alias="LOGIN_LOCKOUT_MINUTES")
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    storage_root: str = Field(default="./data/uploads", alias="STORAGE_ROOT")
    max_upload_mb: int = Field(default=25, alias="MAX_UPLOAD_MB")
    webhook_delivery_timeout_seconds: int = Field(default=10, alias="WEBHOOK_DELIVERY_TIMEOUT_SECONDS")
    ai_enabled: bool = Field(default=False, alias="AI_ENABLED")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5-coder:3b", alias="OLLAMA_MODEL")
    file_storage_root: str = Field(default="data/uploads", alias="FILE_STORAGE_ROOT")
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, alias="MAX_UPLOAD_BYTES")

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

settings = get_settings()
