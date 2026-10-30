import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _production_settings(**values: str) -> Settings:
    base = {
        "APP_ENV": "production",
        "DATABASE_URL": "postgresql+asyncpg://test:test@db.example.test:5432/kalam",
        "REDIS_URL": "redis://redis.example.test:6379/0",
        "COOKIE_SECURE": "true",
        "API_DOCS_ENABLED": "false",
        "DEV_EMAIL_SINK": "false",
        "INTEGRATION_ALLOW_PRIVATE_URLS": "false",
        "STORAGE_BACKEND": "s3",
        "S3_BUCKET": "kalam-test-bucket",
        "OUTBOUND_HTTP_PROXY": "http://proxy.example:8080",
        "FILE_SCAN_PROVIDER": "clamd",
    }
    base.update(values)
    return Settings(_env_file=None, **base)


def test_production_rejects_missing_database_url_instead_of_falling_back_to_sqlite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="Production requires a valid PostgreSQL DATABASE_URL"):
        Settings(
            _env_file=None,
            APP_ENV="production",
            REDIS_URL="redis://redis.example.test:6379/0",
            COOKIE_SECURE=True,
            API_DOCS_ENABLED=False,
            DEV_EMAIL_SINK=False,
            INTEGRATION_ALLOW_PRIVATE_URLS=False,
            STORAGE_BACKEND="s3",
            S3_BUCKET="kalam-test-bucket",
            OUTBOUND_HTTP_PROXY="http://proxy.example:8080",
            FILE_SCAN_PROVIDER="clamd",
        )


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite+aiosqlite:///./data/kalam-local.sqlite3",
        "postgresql+asyncpg://<DB_USER>:<DB_PASSWORD>@db.example.test/kalam",
        "postgresql+asyncpg://DB_USER:DB_PASSWORD@db.example.test/kalam",
        "",
    ],
)
def test_production_rejects_sqlite_and_database_url_placeholders(database_url: str) -> None:
    with pytest.raises(ValidationError, match="Production requires a valid PostgreSQL DATABASE_URL"):
        _production_settings(DATABASE_URL=database_url)


def test_development_placeholder_database_url_uses_local_sqlite_fallback() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="development",
        DATABASE_URL="postgresql+asyncpg://DB_USER:DB_PASSWORD@db.example.test/kalam",
        REDIS_URL="redis://localhost:6379/0",
    )
    assert settings.database_url == "sqlite+aiosqlite:///./data/kalam-local.sqlite3"


def test_production_accepts_valid_postgresql_url_with_encoded_special_character() -> None:
    settings = _production_settings(
        DATABASE_URL="postgresql+asyncpg://user:p%2Aword@db.example.test:5432/kalam"
    )
    assert settings.database_url.startswith("postgresql+asyncpg://")
