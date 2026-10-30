"""Idempotent SaaS renewal task reconciliation shared by API and worker."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CRMAccount, CRMSubscription, CRMTask


async def reconcile_renewal_tasks(
    db: AsyncSession, ops_tenant_id: UUID, horizon_days: int = 120,
) -> dict[str, int]:
    # Serialize manual and scheduled runs for one operations tenant.
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
        {"key": f"crm-renewals:{ops_tenant_id}"},
    )
    horizon = datetime.now(UTC) + timedelta(days=horizon_days)
    rows = (await db.execute(
        select(CRMSubscription, CRMAccount)
        .join(CRMAccount, CRMAccount.id == CRMSubscription.account_id)
        .where(
            CRMSubscription.ops_tenant_id == ops_tenant_id,
            CRMAccount.ops_tenant_id == ops_tenant_id,
            CRMSubscription.status == "active",
            CRMSubscription.renews_at.is_not(None),
            CRMSubscription.renews_at <= horizon,
        )
        .order_by(CRMSubscription.renews_at)
    )).all()
    created = updated = skipped = 0
    for subscription, account in rows:
        if subscription.renews_at is None:
            continue
        for milestone_days in (90, 60, 30):
            due_at = subscription.renews_at - timedelta(days=milestone_days)
            if due_at > horizon:
                continue
            source_key = f"renewal:{subscription.id}:{milestone_days}"
            description = (
                "Review commercial scope, usage context, stakeholder alignment and renewal terms "
                f"before the subscription renewal date {subscription.renews_at.date().isoformat()}."
            )
            existing = await db.scalar(select(CRMTask).where(
                CRMTask.ops_tenant_id == ops_tenant_id,
                CRMTask.source_key == source_key,
            ))
            if existing is not None:
                if existing.status == "open" and existing.due_at != due_at:
                    existing.due_at = due_at
                    existing.description = description
                    updated += 1
                else:
                    skipped += 1
                continue
            priority = "urgent" if milestone_days == 30 else "high" if milestone_days == 60 else "normal"
            db.add(CRMTask(
                ops_tenant_id=ops_tenant_id,
                account_id=account.id,
                subscription_id=subscription.id,
                owner_user_id=account.owner_user_id,
                task_type="renewal",
                title=f"{milestone_days}-day renewal review — {account.name}",
                description=description,
                status="open",
                priority=priority,
                due_at=due_at,
                source_key=source_key,
            ))
            created += 1
    return {
        "created": created, "updated": updated, "skipped": skipped,
        "subscriptions_considered": len(rows),
    }
