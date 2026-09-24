from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("corplms.email")

def send_email(*, recipient: str, subject: str, text: str) -> None:
    if settings.smtp_host and settings.smtp_from:
        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(text)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
            if settings.smtp_starttls:
                client.starttls()
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password or "")
            client.send_message(message)
        return

    if settings.app_env == "development" and settings.dev_email_sink:
        logger.warning(
            "DEV_EMAIL_SINK recipient=%s subject=%s body=%s",
            recipient,
            subject,
            text,
        )
        return

    raise RuntimeError("Email delivery is not configured")
