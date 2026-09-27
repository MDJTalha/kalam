import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.db.session import SessionLocal

async def main():
    async with SessionLocal() as db:
        rows = (await db.execute(text("""
            SELECT id, name, report_type, tenant_id
            FROM saved_reports
            ORDER BY created_at DESC
            LIMIT 5
        """))).mappings().all()
        for row in rows:
            print(dict(row))
        print("SCHEDULES")
        schedules = (await db.execute(text("""
            SELECT id, saved_report_id, status, next_run_at
            FROM report_schedules
            ORDER BY next_run_at
            LIMIT 10
        """))).mappings().all()
        for row in schedules:
            print(dict(row))

asyncio.run(main())
