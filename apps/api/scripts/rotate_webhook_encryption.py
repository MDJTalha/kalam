from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.config import settings
from app.db.models import WebhookEndpoint
from app.db.session import SessionLocal
from app.services.webhook_secrets import reencrypt_webhook_secret


async def rotate() -> int:
    if not settings.webhook_encryption_keys:
        raise RuntimeError("WEBHOOK_ENCRYPTION_KEYS is not configured")

    rotated = 0
    async with SessionLocal() as db:
        result = await db.execute(
            select(WebhookEndpoint).where(
                WebhookEndpoint.secret_encrypted.is_not(None)
            )
        )
        for endpoint in result.scalars().all():
            if endpoint.secret_key_id == settings.webhook_active_key_id:
                continue
            (
                endpoint.secret_encrypted,
                endpoint.secret_key_id,
            ) = reencrypt_webhook_secret(
                endpoint.secret_encrypted,
                endpoint.secret_key_id,
            )
            rotated += 1

        await db.commit()
    return rotated
def main() -> None:
    rotated = asyncio.run(rotate())
    print(
        f"WEBHOOK_ENCRYPTION_ROTATION_OK active_key_id="
        f"{settings.webhook_active_key_id} rotated={rotated}"
    )


if __name__ == "__main__":
    main()
