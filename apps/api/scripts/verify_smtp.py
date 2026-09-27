from __future__ import annotations

import argparse
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings


def verify_smtp(recipient: str | None) -> None:
    if not settings.smtp_host or not settings.smtp_from:
        print("SMTP_NOT_CONFIGURED")
        raise SystemExit(2)
    if settings.smtp_username and not settings.smtp_password:
        print("SMTP_PASSWORD_MISSING")
        raise SystemExit(2)

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=15,
    ) as client:
        client.ehlo()
        if settings.smtp_starttls:
            client.starttls()
            client.ehlo()
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password or "")

        print("SMTP_CONNECTION_AND_AUTH_OK")
        if recipient:
            message = EmailMessage()
            message["From"] = settings.smtp_from
            message["To"] = recipient
            message["Subject"] = "Corporate LMS SMTP verification"
            message.set_content(
                "This message verifies the Corporate LMS production SMTP path."
            )
            client.send_message(message)
            print("SMTP_EXTERNAL_DELIVERY_ACCEPTED")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify Corporate LMS SMTP connectivity and optionally send a test message."
    )
    parser.add_argument(
        "--recipient",
        help="Real mailbox to receive an external verification message.",
    )
    args = parser.parse_args()

    try:
        verify_smtp(args.recipient)
    except (OSError, TimeoutError, smtplib.SMTPException) as exc:
        print(f"SMTP_VERIFICATION_FAILED: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
