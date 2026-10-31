from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.config import settings
from app.db.models import (
    CRMAccount,
    CRMContract,
    CRMInvoice,
    CRMPayment,
    CRMSubscription,
    Tenant,
    User,
)
from app.db.session import get_db
from app.services.audit import audit

router = APIRouter()


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


async def _account(db: AsyncSession, tenant_id: UUID, account_id: UUID) -> CRMAccount:
    item = await db.scalar(select(CRMAccount).where(CRMAccount.id == account_id, CRMAccount.ops_tenant_id == tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="CRM account not found")
    return item


async def _subscription(db: AsyncSession, tenant_id: UUID, subscription_id: UUID | None) -> CRMSubscription | None:
    if subscription_id is None:
        return None
    item = await db.scalar(select(CRMSubscription).where(CRMSubscription.id == subscription_id, CRMSubscription.ops_tenant_id == tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return item


async def _reconcile_invoice(db: AsyncSession, invoice: CRMInvoice) -> dict[str, Any]:
    paid = await db.scalar(
        select(func.coalesce(func.sum(CRMPayment.amount_minor), 0)).where(
            CRMPayment.invoice_id == invoice.id,
            CRMPayment.ops_tenant_id == invoice.ops_tenant_id,
            CRMPayment.status == "received",
        )
    )
    paid_minor = int(paid or 0)
    outstanding = max(0, invoice.total_minor - paid_minor)
    now = datetime.now(timezone.utc)
    if paid_minor >= invoice.total_minor and invoice.total_minor > 0:
        invoice.status = "paid"
        if invoice.paid_at is None:
            invoice.paid_at = now
    elif paid_minor > 0:
        invoice.status = "partially_paid"
        invoice.paid_at = None
    elif invoice.due_at and invoice.due_at < now and invoice.status not in {"draft", "void"}:
        invoice.status = "overdue"
        invoice.paid_at = None
    elif invoice.status not in {"draft", "void"}:
        invoice.status = "issued"
        invoice.paid_at = None
    return {"paid_minor": paid_minor, "outstanding_minor": outstanding}


class ContractCreate(BaseModel):
    account_id: UUID
    subscription_id: UUID | None = None
    reference: str = Field(min_length=2, max_length=160)
    status: str = Field(default="draft", max_length=30)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_value_minor: int = Field(default=0, ge=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    signed_at: datetime | None = None
    renewal_terms: str | None = None
    notes: str | None = None


class ContractUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=30)
    total_value_minor: int | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    signed_at: datetime | None = None
    renewal_terms: str | None = None
    notes: str | None = None


class InvoiceCreate(BaseModel):
    account_id: UUID
    subscription_id: UUID | None = None
    contract_id: UUID | None = None
    invoice_number: str = Field(min_length=2, max_length=120)
    status: str = Field(default="draft", pattern="^(draft|issued)$")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    amount_minor: int = Field(default=0, ge=0)
    tax_minor: int = Field(default=0, ge=0)
    issued_at: datetime | None = None
    due_at: datetime | None = None
    external_ref: str | None = Field(default=None, max_length=180)
    notes: str | None = None


class InvoiceUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(draft|issued|void)$")
    amount_minor: int | None = Field(default=None, ge=0)
    tax_minor: int | None = Field(default=None, ge=0)
    issued_at: datetime | None = None
    due_at: datetime | None = None
    external_ref: str | None = Field(default=None, max_length=180)
    notes: str | None = None


class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    received_at: datetime | None = None
    method: str | None = Field(default=None, max_length=60)
    reference: str | None = Field(default=None, max_length=180)
    notes: str | None = None


class PaymentUpdate(BaseModel):
    status: str = Field(pattern="^(received|reversed)$")
    notes: str | None = None


@router.get("/crm/finance/overview")
async def finance_overview(user: User = Depends(_require_ops_user), db: AsyncSession = Depends(get_db)):
    invoice_rows = (await db.execute(
        select(
            CRMInvoice.currency,
            func.coalesce(func.sum(CRMInvoice.total_minor), 0),
            func.count(CRMInvoice.id),
        ).where(
            CRMInvoice.ops_tenant_id == user.tenant_id,
            CRMInvoice.status.notin_(["draft", "void"]),
        ).group_by(CRMInvoice.currency).order_by(CRMInvoice.currency)
    )).all()
    payment_rows = (await db.execute(
        select(
            CRMPayment.currency,
            func.coalesce(func.sum(CRMPayment.amount_minor), 0),
            func.count(CRMPayment.id),
        ).where(
            CRMPayment.ops_tenant_id == user.tenant_id,
            CRMPayment.status == "received",
        ).group_by(CRMPayment.currency).order_by(CRMPayment.currency)
    )).all()
    invoice_status_rows = (await db.execute(
        select(CRMInvoice.status, func.count(CRMInvoice.id))
        .where(CRMInvoice.ops_tenant_id == user.tenant_id)
        .group_by(CRMInvoice.status)
    )).all()
    invoice_counts = {status: int(count or 0) for status, count in invoice_status_rows}
    payment_count = await db.scalar(select(func.count()).select_from(CRMPayment).where(CRMPayment.ops_tenant_id == user.tenant_id))
    active_contracts = await db.scalar(select(func.count()).select_from(CRMContract).where(
        CRMContract.ops_tenant_id == user.tenant_id,
        CRMContract.status == "active",
    ))
    return {
        "invoiced_by_currency": [{"currency": c, "amount_minor": int(v or 0), "invoices": int(n or 0)} for c, v, n in invoice_rows],
        "received_by_currency": [{"currency": c, "amount_minor": int(v or 0), "payments": int(n or 0)} for c, v, n in payment_rows],
        "invoice_counts": {"total": sum(invoice_counts.values()), "open": invoice_counts.get("issued", 0) + invoice_counts.get("partially_paid", 0) + invoice_counts.get("overdue", 0), "overdue": invoice_counts.get("overdue", 0), "paid": invoice_counts.get("paid", 0)},
        "payment_count": int(payment_count or 0),
        "active_contracts": int(active_contracts or 0),
    }


@router.get("/crm/contracts")
async def list_contracts(
    account_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMContract).where(CRMContract.ops_tenant_id == user.tenant_id)
    if account_id is not None:
        stmt = stmt.where(CRMContract.account_id == account_id)
    items = (await db.execute(stmt.order_by(CRMContract.updated_at.desc()).limit(limit))).scalars().all()
    return [{
        "id": str(x.id), "account_id": str(x.account_id),
        "subscription_id": str(x.subscription_id) if x.subscription_id else None,
        "reference": x.reference, "status": x.status, "currency": x.currency,
        "total_value_minor": x.total_value_minor, "starts_at": x.starts_at,
        "ends_at": x.ends_at, "signed_at": x.signed_at,
        "renewal_terms": x.renewal_terms, "notes": x.notes,
    } for x in items]


@router.post("/crm/contracts", status_code=201)
async def create_contract(payload: ContractCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    await _account(db, user.tenant_id, payload.account_id)
    sub = await _subscription(db, user.tenant_id, payload.subscription_id)
    if sub and sub.account_id != payload.account_id:
        raise HTTPException(status_code=422, detail="Subscription does not belong to this account")
    if payload.starts_at and payload.ends_at and payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=422, detail="Contract end must be after contract start")
    item = CRMContract(ops_tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.contract.created", entity_type="crm_contract", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "reference": item.reference, "status": item.status}


@router.patch("/crm/contracts/{contract_id}")
async def update_contract(contract_id: UUID, payload: ContractUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMContract).where(CRMContract.id == contract_id, CRMContract.ops_tenant_id == user.tenant_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    values = payload.model_dump(exclude_unset=True)
    future_start = values.get("starts_at", item.starts_at)
    future_end = values.get("ends_at", item.ends_at)
    if future_start and future_end and future_end <= future_start:
        raise HTTPException(status_code=422, detail="Contract end must be after contract start")
    for key, value in values.items():
        setattr(item, key, value)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.contract.updated", entity_type="crm_contract", entity_id=str(item.id), metadata={"changed_fields": sorted(values)})
    await db.commit()
    return {"id": str(item.id), "status": item.status}


@router.get("/crm/invoices")
async def list_invoices(
    account_id: UUID | None = Query(default=None),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMInvoice).where(CRMInvoice.ops_tenant_id == user.tenant_id)
    if account_id is not None:
        stmt = stmt.where(CRMInvoice.account_id == account_id)
    items = (await db.execute(stmt.order_by(CRMInvoice.due_at.asc().nullslast(), CRMInvoice.created_at.desc()).limit(limit))).scalars().all()
    account_name_rows = (await db.execute(select(CRMAccount.id, CRMAccount.name).where(CRMAccount.ops_tenant_id == user.tenant_id))).all()
    account_names: dict[UUID, str] = {row[0]: row[1] for row in account_name_rows}
    result = []
    changed = False
    for item in items:
        before = item.status
        reconciliation = await _reconcile_invoice(db, item)
        if before != item.status:
            changed = True
        result.append({
            "id": str(item.id), "account_id": str(item.account_id),
            "account_name": account_names.get(item.account_id, "Unknown account"),
            "subscription_id": str(item.subscription_id) if item.subscription_id else None,
            "contract_id": str(item.contract_id) if item.contract_id else None,
            "invoice_number": item.invoice_number, "status": item.status,
            "currency": item.currency, "amount_minor": item.amount_minor,
            "tax_minor": item.tax_minor, "total_minor": item.total_minor,
            "paid_minor": reconciliation["paid_minor"], "outstanding_minor": reconciliation["outstanding_minor"],
            "issued_at": item.issued_at, "due_at": item.due_at, "paid_at": item.paid_at,
            "external_ref": item.external_ref, "notes": item.notes,
        })
    if changed:
        await db.commit()
    return result


@router.get("/crm/page/invoices")
async def paged_invoices(
    account_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=30),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMInvoice, CRMAccount.name).join(CRMAccount, CRMAccount.id == CRMInvoice.account_id).where(CRMInvoice.ops_tenant_id == user.tenant_id, CRMAccount.ops_tenant_id == user.tenant_id)
    if account_id is not None:
        stmt = stmt.where(CRMInvoice.account_id == account_id)
    if status:
        stmt = stmt.where(CRMInvoice.status == status)
    total = int(await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = (await db.execute(stmt.order_by(CRMInvoice.due_at.asc().nullslast(), CRMInvoice.created_at.desc(), CRMInvoice.id).offset(offset).limit(limit))).all()
    items = []
    changed = False
    for item, account_name in rows:
        before = item.status
        reconciliation = await _reconcile_invoice(db, item)
        changed = changed or before != item.status
        items.append({
            "id": str(item.id), "account_id": str(item.account_id), "account_name": account_name,
            "subscription_id": str(item.subscription_id) if item.subscription_id else None, "contract_id": str(item.contract_id) if item.contract_id else None,
            "invoice_number": item.invoice_number, "status": item.status, "currency": item.currency, "amount_minor": item.amount_minor, "tax_minor": item.tax_minor,
            "total_minor": item.total_minor, "paid_minor": reconciliation["paid_minor"], "outstanding_minor": reconciliation["outstanding_minor"],
            "issued_at": item.issued_at, "due_at": item.due_at, "paid_at": item.paid_at, "external_ref": item.external_ref, "notes": item.notes,
        })
    if changed:
        await db.commit()
    return {"total": total, "offset": offset, "limit": limit, "items": items}


@router.post("/crm/invoices", status_code=201)
async def create_invoice(payload: InvoiceCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    await _account(db, user.tenant_id, payload.account_id)
    sub = await _subscription(db, user.tenant_id, payload.subscription_id)
    if sub and sub.account_id != payload.account_id:
        raise HTTPException(status_code=422, detail="Subscription does not belong to this account")
    contract = None
    if payload.contract_id:
        contract = await db.scalar(select(CRMContract).where(CRMContract.id == payload.contract_id, CRMContract.ops_tenant_id == user.tenant_id))
        if contract is None:
            raise HTTPException(status_code=404, detail="Contract not found")
        if contract.account_id != payload.account_id:
            raise HTTPException(status_code=422, detail="Contract does not belong to this account")
        if contract.currency != payload.currency:
            raise HTTPException(status_code=422, detail="Invoice currency must match contract currency")
    if sub and sub.currency != payload.currency:
        raise HTTPException(status_code=422, detail="Invoice currency must match subscription currency")
    if payload.issued_at and payload.due_at and payload.due_at < payload.issued_at:
        raise HTTPException(status_code=422, detail="Invoice due date cannot precede issue date")
    if payload.status == "issued" and payload.amount_minor + payload.tax_minor <= 0:
        raise HTTPException(status_code=422, detail="Issued invoice must have a positive total")
    values = payload.model_dump()
    values["total_minor"] = payload.amount_minor + payload.tax_minor
    item = CRMInvoice(ops_tenant_id=user.tenant_id, **values)
    db.add(item)
    await db.flush()
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.invoice.created", entity_type="crm_invoice", entity_id=str(item.id))
    await db.commit()
    return {"id": str(item.id), "invoice_number": item.invoice_number, "total_minor": item.total_minor, "status": item.status}


@router.patch("/crm/invoices/{invoice_id}")
async def update_invoice(invoice_id: UUID, payload: InvoiceUpdate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMInvoice).where(CRMInvoice.id == invoice_id, CRMInvoice.ops_tenant_id == user.tenant_id).with_for_update())
    if item is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    values = payload.model_dump(exclude_unset=True)
    future_issued = values.get("issued_at", item.issued_at)
    future_due = values.get("due_at", item.due_at)
    if future_issued and future_due and future_due < future_issued:
        raise HTTPException(status_code=422, detail="Invoice due date cannot precede issue date")
    reconciliation = await _reconcile_invoice(db, item)
    new_total = values.get("amount_minor", item.amount_minor) + values.get("tax_minor", item.tax_minor)
    if new_total < reconciliation["paid_minor"]:
        raise HTTPException(status_code=422, detail="Invoice total cannot be lower than received payments")
    if values.get("status") == "void" and reconciliation["paid_minor"] > 0:
        raise HTTPException(status_code=422, detail="Reverse received payments before voiding an invoice")
    if values.get("status") == "draft" and reconciliation["paid_minor"] > 0:
        raise HTTPException(status_code=422, detail="Paid invoice cannot return to draft")
    if values.get("status", item.status) == "issued" and new_total <= 0:
        raise HTTPException(status_code=422, detail="Issued invoice must have a positive total")
    for key, value in values.items():
        setattr(item, key, value)
    item.total_minor = item.amount_minor + item.tax_minor
    await _reconcile_invoice(db, item)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.invoice.updated", entity_type="crm_invoice", entity_id=str(item.id), metadata={"changed_fields": sorted(values)})
    await db.commit()
    return {"id": str(item.id), "status": item.status, "total_minor": item.total_minor}


@router.get("/crm/payments")
async def list_payments(
    account_id: UUID | None = Query(default=None),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMPayment).where(CRMPayment.ops_tenant_id == user.tenant_id)
    if account_id is not None:
        stmt = stmt.where(CRMPayment.account_id == account_id)
    items = (await db.execute(stmt.order_by(CRMPayment.received_at.desc()).limit(limit))).scalars().all()
    account_name_rows = (await db.execute(select(CRMAccount.id, CRMAccount.name).where(CRMAccount.ops_tenant_id == user.tenant_id))).all()
    account_names: dict[UUID, str] = {row[0]: row[1] for row in account_name_rows}
    invoice_number_rows = (await db.execute(select(CRMInvoice.id, CRMInvoice.invoice_number).where(CRMInvoice.ops_tenant_id == user.tenant_id))).all()
    invoice_numbers: dict[UUID, str] = {row[0]: row[1] for row in invoice_number_rows}
    return [{
        "id": str(x.id), "account_id": str(x.account_id), "invoice_id": str(x.invoice_id),
        "account_name": account_names.get(x.account_id, "Unknown account"),
        "invoice_number": invoice_numbers.get(x.invoice_id, "Unknown invoice"),
        "amount_minor": x.amount_minor, "currency": x.currency, "status": x.status,
        "received_at": x.received_at, "method": x.method, "reference": x.reference, "notes": x.notes,
    } for x in items]


@router.get("/crm/page/payments")
async def paged_payments(
    account_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=30),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    user: User = Depends(_require_ops_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CRMPayment, CRMAccount.name, CRMInvoice.invoice_number).join(CRMAccount, CRMAccount.id == CRMPayment.account_id).join(CRMInvoice, CRMInvoice.id == CRMPayment.invoice_id).where(CRMPayment.ops_tenant_id == user.tenant_id, CRMAccount.ops_tenant_id == user.tenant_id, CRMInvoice.ops_tenant_id == user.tenant_id)
    if account_id is not None:
        stmt = stmt.where(CRMPayment.account_id == account_id)
    if status:
        stmt = stmt.where(CRMPayment.status == status)
    total = int(await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = (await db.execute(stmt.order_by(CRMPayment.received_at.desc(), CRMPayment.id).offset(offset).limit(limit))).all()
    return {"total": total, "offset": offset, "limit": limit, "items": [{
        "id": str(x.id), "account_id": str(x.account_id), "invoice_id": str(x.invoice_id), "account_name": account_name, "invoice_number": invoice_number,
        "amount_minor": x.amount_minor, "currency": x.currency, "status": x.status, "received_at": x.received_at, "method": x.method, "reference": x.reference, "notes": x.notes,
    } for x, account_name, invoice_number in rows]}


@router.post("/crm/payments", status_code=201)
async def create_payment(payload: PaymentCreate, user: User = Depends(require_permission("saas.crm.manage")), db: AsyncSession = Depends(get_db)):
    await _require_ops_user(user, db)
    invoice = await db.scalar(select(CRMInvoice).where(CRMInvoice.id == payload.invoice_id, CRMInvoice.ops_tenant_id == user.tenant_id).with_for_update())
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status in {"void", "draft"}:
        raise HTTPException(status_code=422, detail="Issue the invoice before recording a payment")
    if invoice.currency != payload.currency:
        raise HTTPException(status_code=422, detail="Payment currency must match invoice currency")
    reconciliation = await _reconcile_invoice(db, invoice)
    if payload.amount_minor > reconciliation["outstanding_minor"]:
        raise HTTPException(status_code=422, detail="Payment cannot exceed invoice outstanding balance")
    item = CRMPayment(
        ops_tenant_id=user.tenant_id,
        account_id=invoice.account_id,
        invoice_id=invoice.id,
        amount_minor=payload.amount_minor,
        currency=payload.currency,
        status="received",
        received_at=payload.received_at or datetime.now(timezone.utc),
        method=payload.method,
        reference=payload.reference,
        notes=payload.notes,
    )
    db.add(item)
    await db.flush()
    await _reconcile_invoice(db, invoice)
    await audit(db, tenant_id=user.tenant_id, actor_id=user.id, action="crm.payment.received", entity_type="crm_payment", entity_id=str(item.id), metadata={"invoice_id": str(invoice.id), "amount_minor": item.amount_minor, "currency": item.currency})
    await db.commit()
    return {"id": str(item.id), "invoice_id": str(invoice.id), "invoice_status": invoice.status}


@router.patch("/crm/payments/{payment_id}")
async def update_payment(
    payment_id: UUID,
    payload: PaymentUpdate,
    user: User = Depends(require_permission("saas.crm.manage")),
    db: AsyncSession = Depends(get_db),
):
    await _require_ops_user(user, db)
    item = await db.scalar(select(CRMPayment).where(
        CRMPayment.id == payment_id,
        CRMPayment.ops_tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    invoice = await db.scalar(select(CRMInvoice).where(
        CRMInvoice.id == item.invoice_id,
        CRMInvoice.ops_tenant_id == user.tenant_id,
    ).with_for_update())
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    previous_status = item.status
    if payload.status == "received" and previous_status != "received":
        if invoice.status in {"void", "draft"}:
            raise HTTPException(status_code=422, detail="Cannot restore a payment on an unissued or void invoice")
        reconciliation = await _reconcile_invoice(db, invoice)
        if item.amount_minor > reconciliation["outstanding_minor"]:
            raise HTTPException(status_code=422, detail="Restored payment would exceed invoice outstanding balance")
    item.status = payload.status
    if payload.notes is not None:
        item.notes = payload.notes
    await _reconcile_invoice(db, invoice)
    await audit(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="crm.payment.status_changed",
        entity_type="crm_payment",
        entity_id=str(item.id),
        metadata={
            "from": previous_status,
            "to": item.status,
            "invoice_id": str(invoice.id),
        },
    )
    await db.commit()
    return {
        "id": str(item.id),
        "status": item.status,
        "invoice_status": invoice.status,
    }
