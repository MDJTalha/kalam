"""The production worker must execute every queued job family in one cycle."""

import asyncio
import os
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

WORKER_ROOT = Path(__file__).resolve().parents[1].parent / "worker"
MODULE_PATH = WORKER_ROOT / "run.py"
original_directory = Path.cwd()
sys.path.insert(0, str(WORKER_ROOT))
try:
    spec = spec_from_file_location("phase8_worker_run", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    worker = module_from_spec(spec)
    spec.loader.exec_module(worker)
finally:
    os.chdir(original_directory)
    sys.path.remove(str(WORKER_ROOT))


def test_worker_cycle_includes_reminders_compliance_email_webhooks_and_reports(monkeypatch):
    calls = []

    class Session:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def reminders(db):
        calls.append("reminders")
        return {"course_reminders": 1}

    async def compliance(db):
        calls.append("compliance")
        return {"compliance_notifications": 2}

    async def emails():
        calls.append("emails")
        return 3

    async def webhooks():
        calls.append("webhooks")
        return 4

    async def reports():
        calls.append("reports")
        return 5

    async def renewals():
        calls.append("renewals")
        return 6

    monkeypatch.setattr(worker, "SessionLocal", Session)
    monkeypatch.setattr(worker, "run_course_due_reminders", reminders)
    monkeypatch.setattr(worker, "run_compliance_automation", compliance)
    monkeypatch.setattr(worker, "process_notification_emails", emails)
    monkeypatch.setattr(worker, "process_notification_webhooks", webhooks)
    monkeypatch.setattr(worker, "process_scheduled_reports", reports)
    monkeypatch.setattr(worker, "process_saas_renewals", renewals)
    result = asyncio.run(worker.run_once())

    assert calls == ["reminders", "compliance", "emails", "webhooks", "reports", "renewals"]
    assert result == {"course_reminders": 1, "compliance_notifications": 2,
                      "notification_emails_sent": 3, "notification_webhooks_delivered": 4,
                      "scheduled_reports_processed": 5, "crm_renewal_tasks_reconciled": 6}


def test_worker_email_delivery_honors_preferences_but_keeps_security_notifications(monkeypatch):
    class Notification:
        def __init__(self, notification_type, preferences):
            self.notification_type = notification_type
            self.title = notification_type
            self.body = "notification body"
            self.email_sent_at = None
            self.user_id = "user"
            self.tenant_id = "tenant"
            self.preferences = preferences

    class User:
        def __init__(self, preferences):
            self.email = "person@example.com"
            self.preferences = preferences
            self.is_active = True

    rows = [
        (Notification("learning.enrollment", {"notification_preferences": {"email_enabled": False}}), User({"notification_preferences": {"email_enabled": False}})),
        (Notification("security.session_revoked", {"notification_preferences": {"email_enabled": False}}), User({"notification_preferences": {"email_enabled": False}})),
        (Notification("learning.enrollment", {"notification_preferences": {"email_enabled": True, "learning": True}}), User({"notification_preferences": {"email_enabled": True, "learning": True}})),
    ]
    sent = []

    class Result:
        def all(self):
            return rows

    class Session:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def execute(self, statement):
            return Result()
        async def commit(self):
            return None

    monkeypatch.setattr(worker, "SessionLocal", Session)
    monkeypatch.setattr(worker, "send_email", lambda **kwargs: sent.append(kwargs))

    delivered = asyncio.run(worker.process_notification_emails())

    assert delivered == 2
    assert len(sent) == 2
    assert rows[0][0].email_sent_at is None
    assert rows[1][0].email_sent_at is not None
    assert rows[2][0].email_sent_at is not None
