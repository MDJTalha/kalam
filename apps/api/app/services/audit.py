from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import request_id_context
from app.db.models import AuditLog

async def audit(
    db: AsyncSession,
    *,
    tenant_id: UUID | None,
    actor_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    summary: str | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id_context.get(),
            summary=summary,
            record_metadata=metadata or {},
        )
    )
