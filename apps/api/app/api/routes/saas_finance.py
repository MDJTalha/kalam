"""Read-only finance query handlers mounted explicitly by ``app.main``.

Contract, invoice, and payment mutations are implemented by
``saas_commercial``. Keeping this module limited to the finance overview and
paged read models avoids retaining a second, unmounted CRM implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.config import settings
from app.db.models import CRMAccount, CRMContract, CRMInvoice, CRMPayment, Tenant, User
from app.db.session import get_db


async def _ops_tenant(db: AsyncSession) -> Tenant | None:
    slug = settings.saas_ops_tenant_slug or settings.marketing_review_tenant_slug
    if not slug:
        return None
    return await db.scalar(select(Tenant).where(Tenant.slug == slug))


async def _require_ops_user(
    user: User = Depends(require_permission("saas.crm.read")),
    db: AsyncSession = Depends(get_db),
) -> User:
    tenant = await _ops_tenant(db)
    if tenant is None:
        raise HTTPException(status_code=503, detail="SaaS operations tenant is not configured")
    if user.tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="SaaS finance is restricted to the Kalam operations tenant")
    return user


async def _invoice_financials(db: AsyncSession, invoice: CRMInvoice) -> dict[str, Any]:
    paid = await db.scalar(
        select(func.coalesce(func.sum(CRMPayment.amount_minor), 0)).where(
            CRMPayment.invoice_id == invoice.id,
            CRMPayment.ops_tenant_id == invoice.ops_tenant_id,
            CRMPayment.status == "received",
        )
    )
    paid_minor = int(paid or 0)
    outstanding = max(0, invoice.total_minor - paid_minor)
    now = datetime.now(UTC)
    status = invoice.status
    paid_at = invoice.paid_at
    if paid_minor >= invoice.total_minor and invoice.total_minor > 0:
        status = "paid"
        paid_at = paid_at or now
    elif paid_minor > 0:
        status = "partially_paid"
        paid_at = None
    elif invoice.due_at and invoice.due_at < now and status not in {"draft", "void"}:
        status = "overdue"
        paid_at = None
    elif status not in {"draft", "void"}:
        status = "issued"
        paid_at = None
    return {
        "paid_minor": paid_minor,
        "outstanding_minor": outstanding,
        "status": status,
        "paid_at": paid_at,
    }


async def finance_overview(
    user: User = Depends(_require_ops_user), db: AsyncSession = Depends(get_db)
):
    invoice_rows = (
        await db.execute(
            select(
                CRMInvoice.currency,
                func.coalesce(func.sum(CRMInvoice.total_minor), 0),
                func.count(CRMInvoice.id),
            )
            .where(
                CRMInvoice.ops_tenant_id == user.tenant_id,
                CRMInvoice.status.notin_(["draft", "void"]),
            )
            .group_by(CRMInvoice.currency)
            .order_by(CRMInvoice.currency)
        )
    ).all()
    payment_rows = (
        await db.execute(
            select(
                CRMPayment.currency,
                func.coalesce(func.sum(CRMPayment.amount_minor), 0),
                func.count(CRMPayment.id),
            )
            .where(
                CRMPayment.ops_tenant_id == user.tenant_id,
                CRMPayment.status == "received",
            )
            .group_by(CRMPayment.currency)
            .order_by(CRMPayment.currency)
        )
    ).all()
    invoice_status_rows = (
        await db.execute(
            select(CRMInvoice.status, func.count(CRMInvoice.id))
            .where(CRMInvoice.ops_tenant_id == user.tenant_id)
            .group_by(CRMInvoice.status)
        )
    ).all()
    invoice_counts = {status: int(count or 0) for status, count in invoice_status_rows}
    payment_count = await db.scalar(
        select(func.count())
        .select_from(CRMPayment)
        .where(CRMPayment.ops_tenant_id == user.tenant_id)
    )
    active_contracts = await db.scalar(
        select(func.count())
        .select_from(CRMContract)
        .where(
            CRMContract.ops_tenant_id == user.tenant_id,
            CRMContract.status == "active",
        )
    )
    return {
        "invoiced_by_currency": [
            {"currency": c, "amount_minor": int(v or 0), "invoices": int(n or 0)}
            for c, v, n in invoice_rows
        ],
        "received_by_currency": [
            {"currency": c, "amount_minor": int(v or 0), "payments": int(n or 0)}
            for c, v, n in payment_rows
        ],
        "invoice_counts": {
            "total": sum(invoice_counts.values()),
            "open": invoice_counts.get("issued", 0)
            + invoice_counts.get("partially_paid", 0)
            + invoice_counts.get("overdue", 0),
            "overdue": invoice_counts.get("overdue", 0),
            "paid": invoice_counts.get("paid", 0),
        },
        "payment_count": int(payment_count or 0),
        "active_contracts": int(active_contracts or 0),
    }


async def paged_invoices(
    account_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=30),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CRMInvoice, CRMAccount.name)
        .join(CRMAccount, CRMAccount.id == CRMInvoice.account_id)
        .where(
            CRMInvoice.ops_tenant_id == user.tenant_id,
            CRMAccount.ops_tenant_id == user.tenant_id,
        )
    )
    if account_id is not None:
        stmt = stmt.where(CRMInvoice.account_id == account_id)
    if status:
        stmt = stmt.where(CRMInvoice.status == status)
    total = int(await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = (
        await db.execute(
            stmt.order_by(
                CRMInvoice.due_at.asc().nullslast(),
                CRMInvoice.created_at.desc(),
                CRMInvoice.id,
            )
            .offset(offset)
            .limit(limit)
        )
    ).all()
    items = []
    for item, account_name in rows:
        reconciliation = await _invoice_financials(db, item)
        items.append(
            {
                "id": str(item.id),
                "account_id": str(item.account_id),
                "account_name": account_name,
                "subscription_id": str(item.subscription_id) if item.subscription_id else None,
                "contract_id": str(item.contract_id) if item.contract_id else None,
                "invoice_number": item.invoice_number,
                "status": reconciliation["status"],
                "currency": item.currency,
                "amount_minor": item.amount_minor,
                "tax_minor": item.tax_minor,
                "total_minor": item.total_minor,
                "paid_minor": reconciliation["paid_minor"],
                "outstanding_minor": reconciliation["outstanding_minor"],
                "issued_at": item.issued_at,
                "due_at": item.due_at,
                "paid_at": reconciliation["paid_at"],
                "external_ref": item.external_ref,
                "notes": item.notes,
            }
        )
    return {"total": total, "offset": offset, "limit": limit, "items": items}


async def paged_payments(
    account_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=30),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CRMPayment, CRMAccount.name, CRMInvoice.invoice_number)
        .join(CRMAccount, CRMAccount.id == CRMPayment.account_id)
        .join(CRMInvoice, CRMInvoice.id == CRMPayment.invoice_id)
        .where(
            CRMPayment.ops_tenant_id == user.tenant_id,
            CRMAccount.ops_tenant_id == user.tenant_id,
            CRMInvoice.ops_tenant_id == user.tenant_id,
        )
    )
    if account_id is not None:
        stmt = stmt.where(CRMPayment.account_id == account_id)
    if status:
        stmt = stmt.where(CRMPayment.status == status)
    total = int(await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = (
        await db.execute(
            stmt.order_by(CRMPayment.received_at.desc(), CRMPayment.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": str(payment.id),
                "account_id": str(payment.account_id),
                "invoice_id": str(payment.invoice_id),
                "account_name": account_name,
                "invoice_number": invoice_number,
                "amount_minor": payment.amount_minor,
                "currency": payment.currency,
                "status": payment.status,
                "received_at": payment.received_at,
                "method": payment.method,
                "reference": payment.reference,
                "notes": payment.notes,
            }
            for payment, account_name, invoice_number in rows
        ],
    }
