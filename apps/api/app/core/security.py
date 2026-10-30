import hashlib
import secrets
from datetime import UTC, datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

_password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16)

def hash_password(password: str) -> str:
    return _password_hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False

def new_session_token() -> str:
    return secrets.token_urlsafe(48)

def session_token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def support_context_token_hash(raw_support_token: str, raw_session_token: str) -> str:
    """Bind a privileged support context to one exact authenticated session."""
    return session_token_hash(f"{raw_support_token}\x00{raw_session_token}")


def utcnow() -> datetime:
    return datetime.now(UTC)
