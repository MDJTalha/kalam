import pytest

from app.core.security import session_token_hash, support_context_token_hash
from scripts import seed_reference_enterprise


def test_support_context_hash_is_bound_to_exact_login_session() -> None:
    support_token = "high-entropy-support-token"
    first_session = support_context_token_hash(support_token, "login-session-one")
    same_session = support_context_token_hash(support_token, "login-session-one")
    second_session = support_context_token_hash(support_token, "login-session-two")

    assert first_session == same_session
    assert first_session != second_session
    assert first_session != session_token_hash(support_token)


def test_reference_seed_is_disabled_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed_reference_enterprise.settings, "app_env", "production")
    monkeypatch.setattr(
        seed_reference_enterprise.settings,
        "database_url",
        "postgresql+asyncpg://test:test@127.0.0.1:5434/kalam-test",
    )
    monkeypatch.setattr(seed_reference_enterprise, "ADMIN_PASSWORD", "test-only-password")
    monkeypatch.setenv("KALAM_ALLOW_DESTRUCTIVE_REFERENCE_SEED", "true")
    monkeypatch.setenv("KALAM_REFERENCE_SEED_DB_NAME", "kalam-test")

    with pytest.raises(RuntimeError, match="disabled outside development/test/CI"):
        seed_reference_enterprise._assert_safe_reference_seed_target()


def test_reference_seed_requires_explicit_operator_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed_reference_enterprise.settings, "app_env", "development")
    monkeypatch.setattr(
        seed_reference_enterprise.settings,
        "database_url",
        "postgresql+asyncpg://test:test@127.0.0.1:5434/kalam-test",
    )
    monkeypatch.setattr(seed_reference_enterprise, "ADMIN_PASSWORD", "test-only-password")
    monkeypatch.delenv("KALAM_ALLOW_DESTRUCTIVE_REFERENCE_SEED", raising=False)

    with pytest.raises(RuntimeError, match="explicitly authorize"):
        seed_reference_enterprise._assert_safe_reference_seed_target()


def test_reference_seed_requires_database_name_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed_reference_enterprise.settings, "app_env", "development")
    monkeypatch.setattr(
        seed_reference_enterprise.settings,
        "database_url",
        "postgresql+asyncpg://test:test@127.0.0.1:5434/kalam-test",
    )
    monkeypatch.setattr(seed_reference_enterprise, "ADMIN_PASSWORD", "test-only-password")
    monkeypatch.setenv("KALAM_ALLOW_DESTRUCTIVE_REFERENCE_SEED", "true")
    monkeypatch.setenv("KALAM_REFERENCE_SEED_DB_NAME", "different-database")

    with pytest.raises(RuntimeError, match="exactly match"):
        seed_reference_enterprise._assert_safe_reference_seed_target()


def test_reference_seed_rejects_remote_postgresql_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed_reference_enterprise.settings, "app_env", "development")
    monkeypatch.setattr(
        seed_reference_enterprise.settings,
        "database_url",
        "postgresql+asyncpg://test:test@db.example.test:5432/kalam-test",
    )
    monkeypatch.setattr(seed_reference_enterprise, "ADMIN_PASSWORD", "test-only-password")
    monkeypatch.setenv("KALAM_ALLOW_DESTRUCTIVE_REFERENCE_SEED", "true")
    monkeypatch.setenv("KALAM_REFERENCE_SEED_DB_NAME", "kalam-test")

    with pytest.raises(RuntimeError, match="loopback"):
        seed_reference_enterprise._assert_safe_reference_seed_target()
