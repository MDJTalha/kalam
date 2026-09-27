from cryptography.fernet import Fernet

from app.core.config import settings
from app.services.webhook_secrets import (
    WebhookSecretConfigurationError,
    decrypt_webhook_secret,
    encrypt_webhook_secret,
    reencrypt_webhook_secret,
)


def configure_keys(*keys: tuple[str, bytes]) -> None:
    settings.webhook_encryption_keys = ";".join(
        f"{key_id}:{key.decode('ascii')}" for key_id, key in keys
    )
    settings.webhook_active_key_id = keys[0][0]


def test_webhook_secret_round_trip_and_authentication(monkeypatch):
    key = Fernet.generate_key()
    configure_keys(("primary", key))

    encrypted, key_id = encrypt_webhook_secret("webhook-secret-value")

    assert key_id == "primary"
    assert encrypted != "webhook-secret-value"
    assert decrypt_webhook_secret(encrypted, key_id) == "webhook-secret-value"

    tampered = encrypted[:-1] + ("A" if encrypted[-1] != "A" else "B")
    try:
        decrypt_webhook_secret(tampered, key_id)
    except WebhookSecretConfigurationError:
        pass
    else:
        raise AssertionError("tampered webhook ciphertext must be rejected")
def test_webhook_secret_reencrypts_when_active_key_rotates():
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()

    configure_keys(("old", old_key))
    encrypted, key_id = encrypt_webhook_secret("rotate-me")

    settings.webhook_encryption_keys = (
        f"new:{new_key.decode('ascii')};old:{old_key.decode('ascii')}"
    )
    settings.webhook_active_key_id = "new"

    rotated, rotated_key_id = reencrypt_webhook_secret(encrypted, key_id)

    assert rotated_key_id == "new"
    assert decrypt_webhook_secret(rotated, rotated_key_id) == "rotate-me"
    assert rotated != encrypted


def test_webhook_secret_requires_key_configuration():
    settings.webhook_encryption_keys = None
    settings.webhook_active_key_id = "primary"

    try:
        encrypt_webhook_secret("blocked")
    except WebhookSecretConfigurationError:
        pass
    else:
        raise AssertionError("missing encryption keys must fail closed")
