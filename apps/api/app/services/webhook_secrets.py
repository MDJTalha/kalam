from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class WebhookSecretConfigurationError(RuntimeError):
    """Raised when webhook encryption keys are missing or invalid."""


def _keyring() -> dict[str, bytes]:
    raw = settings.webhook_encryption_keys
    if not raw:
        raise WebhookSecretConfigurationError(
            "Webhook encryption keys are not configured"
        )

    keyring: dict[str, bytes] = {}
    for entry in raw.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        try:
            key_id, encoded_key = entry.split(":", 1)
            if not key_id or not encoded_key:
                raise ValueError
            key = encoded_key.encode("ascii")
            Fernet(key)
        except (ValueError, UnicodeEncodeError):
            raise WebhookSecretConfigurationError(
                "Webhook encryption key configuration is invalid"
            ) from None
        keyring[key_id] = key

    if settings.webhook_active_key_id not in keyring:
        raise WebhookSecretConfigurationError(
            "Active webhook encryption key is not configured"
        )
    return keyring
def encrypt_webhook_secret(secret: str) -> tuple[str, str]:
    if not secret:
        raise ValueError("Webhook secret must not be empty")
    keyring = _keyring()
    key_id = settings.webhook_active_key_id
    token = Fernet(keyring[key_id]).encrypt(secret.encode("utf-8"))
    return token.decode("ascii"), key_id


def decrypt_webhook_secret(
    encrypted_secret: str,
    key_id: str | None,
) -> str:
    if not encrypted_secret:
        raise WebhookSecretConfigurationError(
            "Webhook endpoint does not have an encrypted secret"
        )

    keyring = _keyring()
    candidate_ids = []
    if key_id and key_id in keyring:
        candidate_ids.append(key_id)
    candidate_ids.extend(item for item in keyring if item not in candidate_ids)

    for candidate_id in candidate_ids:
        try:
            plaintext = Fernet(keyring[candidate_id]).decrypt(
                encrypted_secret.encode("ascii")
            )
            return plaintext.decode("utf-8")
        except (InvalidToken, ValueError, UnicodeDecodeError):
            continue

    raise WebhookSecretConfigurationError(
        "Webhook secret cannot be decrypted with configured keys"
    )


def reencrypt_webhook_secret(
    encrypted_secret: str,
    key_id: str | None,
) -> tuple[str, str]:
    plaintext = decrypt_webhook_secret(encrypted_secret, key_id)
    return encrypt_webhook_secret(plaintext)
