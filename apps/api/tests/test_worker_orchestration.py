"""The production worker must execute every queued job family in one cycle."""

import asyncio
import os
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

WORKER_ROOT = Path(__file__).resolve().parents[2] / "worker"
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

    monkeypatch.setattr(worker, "SessionLocal", Session)
    monkeypatch.setattr(worker, "run_course_due_reminders", reminders)
    monkeypatch.setattr(worker, "run_compliance_automation", compliance)
    monkeypatch.setattr(worker, "process_notification_emails", emails)
    monkeypatch.setattr(worker, "process_notification_webhooks", webhooks)
    monkeypatch.setattr(worker, "process_scheduled_reports", reports)
    result = asyncio.run(worker.run_once())

    assert calls == ["reminders", "compliance", "emails", "webhooks", "reports"]
    assert result == {"course_reminders": 1, "compliance_notifications": 2,
                      "notification_emails_sent": 3, "notification_webhooks_delivered": 4,
                      "scheduled_reports_processed": 5}
