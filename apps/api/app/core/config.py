from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="Corporate LMS API", alias="APP_NAME")
    database_url: str = Field(default="sqlite+aiosqlite:///./data/kalam-local.sqlite3", alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    database_pool_mode: str = Field(default="auto", alias="DATABASE_POOL_MODE")
    redis_url: str = Field(alias="REDIS_URL")
    web_origin: str = Field(default="http://127.0.0.1:3000", alias="WEB_ORIGIN")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", alias="ALLOWED_HOSTS")
    api_origin: str = Field(default="http://127.0.0.1:8000", alias="API_ORIGIN")
    session_cookie_name: str = Field(default="corp_lms_session", alias="SESSION_COOKIE_NAME")
    session_ttl_seconds: int = Field(default=28800, alias="SESSION_TTL_SECONDS")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_docs_enabled: bool = Field(default=True, alias="API_DOCS_ENABLED")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_starttls: bool = Field(default=True, alias="SMTP_STARTTLS")
    smtp_ssl: bool = Field(default=False, alias="SMTP_SSL")
    smtp_timeout_seconds: int = Field(default=15, alias="SMTP_TIMEOUT_SECONDS")
    dev_email_sink: bool = Field(default=True, alias="DEV_EMAIL_SINK")
    marketing_inbox_enabled: bool = Field(default=False, alias="MARKETING_INBOX_ENABLED")
    marketing_review_tenant_slug: str | None = Field(default=None, alias="MARKETING_REVIEW_TENANT_SLUG")
    saas_ops_tenant_slug: str | None = Field(default=None, alias="SAAS_OPS_TENANT_SLUG")
    saas_demo_crm_enabled: bool = Field(default=False, alias="SAAS_DEMO_CRM_ENABLED")
    saas_demo_tenant_slug: str = Field(default="demo-corporation", alias="SAAS_DEMO_TENANT_SLUG")
    saas_demo_admin_email: str = Field(default="admin@demo.corp", alias="SAAS_DEMO_ADMIN_EMAIL")
    reset_token_minutes: int = Field(default=30, alias="RESET_TOKEN_MINUTES")
    max_failed_login_attempts: int = Field(default=5, alias="MAX_FAILED_LOGIN_ATTEMPTS")
    login_lockout_minutes: int = Field(default=15, alias="LOGIN_LOCKOUT_MINUTES")
    sso_state_key: str | None = Field(default=None, alias="SSO_STATE_KEY")
    sso_transaction_ttl_seconds: int = Field(default=600, alias="SSO_TRANSACTION_TTL_SECONDS")
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    storage_root: str = Field(
        default="./data/uploads",
        alias="FILE_STORAGE_ROOT",
    )
    legacy_storage_root: str | None = Field(default=None, alias="STORAGE_ROOT", exclude=True)
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_endpoint_url: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_access_key_id: str | None = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    max_upload_mb: int = Field(default=25, ge=1, alias="MAX_UPLOAD_MB")
    webhook_delivery_timeout_seconds: int = Field(default=10, alias="WEBHOOK_DELIVERY_TIMEOUT_SECONDS")
    outbound_http_proxy: str | None = Field(default=None, alias="OUTBOUND_HTTP_PROXY")
    webhook_encryption_keys: str | None = Field(default=None, alias="WEBHOOK_ENCRYPTION_KEYS")
    webhook_active_key_id: str = Field(default="primary", alias="WEBHOOK_ACTIVE_KEY_ID")
    integration_allow_private_urls: bool = Field(default=True, alias="INTEGRATION_ALLOW_PRIVATE_URLS")
    ai_enabled: bool = Field(default=False, alias="AI_ENABLED")
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, gt=0, alias="MAX_UPLOAD_BYTES")
    file_scan_provider: str = Field(default="none", alias="FILE_SCAN_PROVIDER")
    file_scan_host: str = Field(default="127.0.0.1", alias="FILE_SCAN_HOST")
    file_scan_port: int = Field(default=3310, alias="FILE_SCAN_PORT")
    file_scan_timeout_seconds: int = Field(default=30, alias="FILE_SCAN_TIMEOUT_SECONDS")

    @model_validator(mode="after")
    def normalize_runtime_configuration(self) -> "Settings":
        raw_database_url = (self.database_url or "").strip()
        environment = self.app_env.strip().lower()
        lowered_url = raw_database_url.lower()
        placeholder_markers = (
            "<db_",
            "db_user",
            "db_password",
            "change_me",
            "changeme",
            "replace_me",
            "replace-me",
            "your_database",
            "your_db",
            "<",
            ">",
        )
        is_placeholder = not raw_database_url or any(
            marker in lowered_url for marker in placeholder_markers
        )

        if environment in {"production", "prod"}:
            # Never silently start production against a local SQLite file. A typo,
            # unexpanded template variable, or missing secret must stop startup.
            if is_placeholder or not lowered_url.startswith(("postgresql://", "postgresql+")):
                raise ValueError(
                    "Production requires a valid PostgreSQL DATABASE_URL; "
                    "SQLite and placeholder values are not permitted."
                )
        elif is_placeholder:
            # SQLite remains an explicit local/test fallback only.
            self.database_url = "sqlite+aiosqlite:///./data/kalam-local.sqlite3"
        return self

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if "storage_root" not in self.model_fields_set and self.legacy_storage_root is not None:
            self.storage_root = self.legacy_storage_root
        if self.storage_backend.lower() not in {"local", "s3"}:
            raise ValueError("STORAGE_BACKEND must be either 'local' or 's3'")
        if self.file_scan_provider.lower().strip() not in {"none", "clamd"}:
            raise ValueError("FILE_SCAN_PROVIDER must be either 'none' or 'clamd'")
        if bool(self.s3_access_key_id) != bool(self.s3_secret_access_key):
            raise ValueError("S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY must be configured together")
        if self.storage_backend.lower() == "s3" and not self.s3_bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        if self.outbound_http_proxy:
            from urllib.parse import urlparse

            proxy = urlparse(self.outbound_http_proxy)
            if proxy.scheme not in {"http", "https"} or not proxy.hostname or proxy.username or proxy.password:
                raise ValueError("OUTBOUND_HTTP_PROXY must be an HTTP(S) proxy URL without embedded credentials")
        if self.app_env.lower() in {"production", "prod"}:
            unsafe = []
            if not self.cookie_secure:
                unsafe.append("COOKIE_SECURE=true")
            if self.api_docs_enabled:
                unsafe.append("API_DOCS_ENABLED=false")
            if self.dev_email_sink:
                unsafe.append("DEV_EMAIL_SINK=false")
            if self.integration_allow_private_urls:
                unsafe.append("INTEGRATION_ALLOW_PRIVATE_URLS=false")
            if self.storage_backend.lower() != "s3":
                unsafe.append("STORAGE_BACKEND=s3")
            if self.file_scan_provider.lower().strip() != "clamd":
                unsafe.append("FILE_SCAN_PROVIDER=clamd (malware scanning required in production)")
            if not self.outbound_http_proxy:
                unsafe.append("OUTBOUND_HTTP_PROXY (SSRF-safe egress proxy)")
            if unsafe:
                raise ValueError("Production safety requirements not met: " + ", ".join(unsafe))
        return self

    @property
    def upload_limit_bytes(self) -> int:
        """Use the byte-based setting when supplied; retain the legacy MB knob."""
        if "max_upload_bytes" in self.model_fields_set:
            return self.max_upload_bytes
        return self.max_upload_mb * 1024 * 1024

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

settings = get_settings()
