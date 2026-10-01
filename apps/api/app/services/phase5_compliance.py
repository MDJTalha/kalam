from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Tenant
from app.services.compliance_operations import run_compliance_operations_for_tenant


async def run_compliance_automation(db: AsyncSession) -> dict[str, int]:
    """Worker-compatible tenant-wide compliance control loop.

    Phase 8 is the single source of truth for overdue normalization, exception
    expiry, recurrence, escalation and notifications. The worker has no user actor,
    so audit events are recorded as system actions while preserving tenant scope.
    """
    tenants = (await db.scalars(select(Tenant).where(Tenant.status == "active"))).all()
    totals = {
        "compliance_overdue": 0,
        "compliance_exceptions_expired": 0,
        "compliance_recurring": 0,
        "compliance_escalations": 0,
    }
    for tenant in tenants:
        result = await run_compliance_operations_for_tenant(db, tenant.id, None)
        totals["compliance_overdue"] += int(result["overdue"])
        totals["compliance_exceptions_expired"] += int(result["expired_exceptions"])
        totals["compliance_recurring"] += int(result["recurring_created"])
        totals["compliance_escalations"] += int(result["escalated"])
    return totals
