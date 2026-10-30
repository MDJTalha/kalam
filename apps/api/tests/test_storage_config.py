import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(**values: str) -> Settings:
    # Keep config tests deterministic even when the caller runs the suite with
    # production-like environment variables such as FILE_SCAN_PROVIDER=clamd.
    values.setdefault("FILE_SCAN_PROVIDER", "none")
    # Settings reads process environment variables even when dotenv loading is
    # disabled. Clear them so each test exercises only its explicit arguments.
    with patch.dict(os.environ, {}, clear=True):
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
            REDIS_URL="redis://localhost:6379/0",
            **values,
        )


def test_canonical_storage_environment_settings_are_honored() -> None:
    settings = _settings(FILE_STORAGE_ROOT="/srv/kalam/uploads", MAX_UPLOAD_BYTES="4096")

    assert settings.storage_root == "/srv/kalam/uploads"
    assert settings.upload_limit_bytes == 4096


def test_legacy_storage_environment_settings_remain_compatible() -> None:
    settings = _settings(STORAGE_ROOT="/srv/legacy-uploads", MAX_UPLOAD_MB="3")

    assert settings.storage_root == "/srv/legacy-uploads"
    assert settings.upload_limit_bytes == 3 * 1024 * 1024


def test_canonical_storage_path_takes_precedence_over_legacy_alias() -> None:
    settings = _settings(
        FILE_STORAGE_ROOT="/srv/current-uploads",
        STORAGE_ROOT="/srv/legacy-uploads",
    )

    assert settings.storage_root == "/srv/current-uploads"


def test_byte_upload_limit_takes_precedence_when_both_forms_are_set() -> None:
    settings = _settings(MAX_UPLOAD_BYTES="2048", MAX_UPLOAD_MB="3")

    assert settings.upload_limit_bytes == 2048


def test_s3_backend_requires_bucket() -> None:
    with pytest.raises(ValidationError, match="S3_BUCKET is required"):
        _settings(STORAGE_BACKEND="s3")


def test_production_requires_s3_storage() -> None:
    with pytest.raises(ValidationError, match="STORAGE_BACKEND=s3"):
        Settings(
            _env_file=None,
            APP_ENV="production",
            DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
            REDIS_URL="redis://localhost:6379/0",
            COOKIE_SECURE=True,
            API_DOCS_ENABLED=False,
            DEV_EMAIL_SINK=False,
            INTEGRATION_ALLOW_PRIVATE_URLS=False,
        )



def test_file_scan_provider_rejects_unknown_values() -> None:
    with pytest.raises(ValidationError, match="FILE_SCAN_PROVIDER"):
        _settings(FILE_SCAN_PROVIDER="unknown-scanner")


def test_production_requires_configured_malware_scanning() -> None:
    with pytest.raises(ValidationError, match="FILE_SCAN_PROVIDER=clamd"):
        _settings(
            APP_ENV="production",
            COOKIE_SECURE="true",
            API_DOCS_ENABLED="false",
            DEV_EMAIL_SINK="false",
            INTEGRATION_ALLOW_PRIVATE_URLS="false",
            STORAGE_BACKEND="s3",
            S3_BUCKET="kalam-test-bucket",
            OUTBOUND_HTTP_PROXY="http://proxy.example:8080",
        )


def test_production_accepts_clamd_when_other_safety_gates_pass() -> None:
    settings = _settings(
        APP_ENV="production",
        COOKIE_SECURE="true",
        API_DOCS_ENABLED="false",
        DEV_EMAIL_SINK="false",
        INTEGRATION_ALLOW_PRIVATE_URLS="false",
        STORAGE_BACKEND="s3",
        S3_BUCKET="kalam-test-bucket",
        OUTBOUND_HTTP_PROXY="http://proxy.example:8080",
        FILE_SCAN_PROVIDER="clamd",
    )

    assert settings.file_scan_provider == "clamd"
