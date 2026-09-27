import smtplib

import pytest

from app.core.config import settings
from app.services.email import send_email


def test_smtp_transport_errors_are_retryable(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.test")
    monkeypatch.setattr(settings, "smtp_from", "lms@example.test")
    monkeypatch.setattr(settings, "smtp_username", "user")
    monkeypatch.setattr(settings, "smtp_password", "password")
    monkeypatch.setattr(settings, "smtp_starttls", True)

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def ehlo(self):
            return None

        def starttls(self):
            return None

        def login(self, username, password):
            return None

        def send_message(self, message):
            raise smtplib.SMTPException("provider rejected message")

    monkeypatch.setattr("app.services.email.smtplib.SMTP", lambda *args, **kwargs: Client())

    with pytest.raises(RuntimeError, match="SMTP delivery failed"):
        send_email(
            recipient="learner@example.test",
            subject="Test",
            text="Test",
        )
