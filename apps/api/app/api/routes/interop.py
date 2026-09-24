import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.models import LearningStatement, User
from app.db.session import get_db

router = APIRouter()


class XApiStatement(BaseModel):
    id: str | None = Field(default=None, min_length=8, max_length=120)
    verb: dict
    object: dict


@router.post("/xapi/statements", status_code=202)
async def receive_xapi_statement(
    statement: XApiStatement,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    statement_id = statement.id or str(uuid.uuid4())
    verb_id = str(statement.verb.get("id") or "")
    object_id = str(statement.object.get("id") or "")
    if not verb_id or not object_id:
        raise HTTPException(status_code=422, detail="xAPI statement requires verb.id and object.id")

    existing = await db.scalar(
        select(LearningStatement).where(
            LearningStatement.tenant_id == user.tenant_id,
            LearningStatement.statement_id == statement_id,
        )
    )
    if existing:
        return {"statement_id": statement_id, "status": "duplicate"}

    db.add(
        LearningStatement(
            tenant_id=user.tenant_id,
            statement_id=statement_id,
            actor_user_id=user.id,
            verb=verb_id,
            object_id=object_id,
            statement=statement.model_dump(),
        )
    )
    await db.commit()
    return {"statement_id": statement_id, "status": "accepted"}


@router.get("/xapi/statements")
async def list_xapi_statements(
    limit: int = 100,
    user: User = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(limit, 500))
    result = await db.execute(
        select(LearningStatement)
        .where(LearningStatement.tenant_id == user.tenant_id)
        .order_by(LearningStatement.recorded_at.desc())
        .limit(limit)
    )
    return [item.statement for item in result.scalars().all()]
