import asyncio
import subprocess
import sys
from pathlib import Path
from uuid import uuid4
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "api"
WORKER_ROOT = ROOT / "worker"
sys.path.insert(0, str(API_ROOT))
sys.path.insert(0, str(WORKER_ROOT))

from app.core.security import utcnow
from app.db.session import SessionLocal
from report_scheduler import process_scheduled_reports

async def main():
    report_id = uuid4()
    schedule_id = uuid4()
    async with SessionLocal() as db:
        tenant = (await db.execute(text("SELECT id FROM tenants WHERE slug='demo-corporation' LIMIT 1"))).scalar_one()
        owner = (await db.execute(text("SELECT id FROM users WHERE tenant_id=:t AND email='admin@demo.corp' LIMIT 1"), {"t": tenant})).scalar_one()
        await db.execute(text("""
            INSERT INTO saved_reports (id, tenant_id, owner_id, name, report_type, definition, visibility, enabled, created_at, updated_at)
            VALUES (:id, :t, :o, :name, 'executive_summary', '{}'::jsonb, 'private', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """), {"id": report_id, "t": tenant, "o": owner, "name": f"Phase 6 Scheduler Evidence {report_id}"})
        await db.execute(text("""
            INSERT INTO report_schedules (id, tenant_id, saved_report_id, frequency, next_run_at, recipients, status, created_at, updated_at)
            VALUES (:id, :t, :r, 'daily', :run, '["learner@demo.corp"]'::jsonb, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """), {"id": schedule_id, "t": tenant, "r": report_id, "run": utcnow()})
        await db.commit()
    worker = subprocess.run(
        [sys.executable, str(WORKER_ROOT / "run.py"), "--once"],
        cwd=WORKER_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    processed = 1 if worker.returncode == 0 else 0
    print("WORKER_EXIT_CODE=", worker.returncode)
    print("WORKER_OUTPUT=", worker.stdout.strip())
    if worker.stderr.strip():
        print("WORKER_STDERR=", worker.stderr.strip())
    async with SessionLocal() as db:
        run = (await db.execute(text("""
            SELECT status, output_metadata, error, started_at, completed_at
            FROM report_schedule_runs WHERE schedule_id=:s ORDER BY started_at DESC LIMIT 1
        """), {"s": schedule_id})).mappings().one_or_none()
        await db.execute(text("UPDATE report_schedules SET status='paused', updated_at=CURRENT_TIMESTAMP WHERE id=:s"), {"s": schedule_id})
        await db.commit()
        print("SCHEDULED_REPORTS_PROCESSED=", processed)
        print("RUN_EVIDENCE=", dict(run) if run else None)

asyncio.run(main())
