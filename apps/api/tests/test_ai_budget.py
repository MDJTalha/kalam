import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select

from app.api.routes.ai import _daily_token_usage, _enforce_daily_token_budget
from app.db.models import AIInteraction, AIGovernancePolicy, Tenant, User
from app.db.session import SessionLocal


@pytest.mark.asyncio
async def test_daily_token_budget_blocks_when_reached():
    async with SessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "demo-corporation"))
        user = await db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == "admin@demo.corp"))
        policy = await db.scalar(select(AIGovernancePolicy).where(AIGovernancePolicy.tenant_id == tenant.id))
        assert tenant is not None and user is not None and policy is not None
        previous_budget = policy.daily_token_budget
        previous_enabled = policy.enabled
        interaction = AIInteraction(
            tenant_id=tenant.id,
            user_id=user.id,
            request_type="budget_test",
            provider="test",
            model="test",
            source_ids=[],
            prompt_hash="0" * 64,
            allowed=True,
            response_summary="Budget test.",
            latency_ms=1,
            input_tokens=10,
            output_tokens=5,
        )
        db.add(interaction)
        policy.daily_token_budget = 1
        policy.enabled = True
        await db.commit()
        try:
            usage = await _daily_token_usage(db, tenant.id)
            assert usage >= 15
            with pytest.raises(HTTPException) as exc:
                await _enforce_daily_token_budget(db, tenant.id, policy)
            assert exc.value.status_code == 429
        finally:
            await db.execute(delete(AIInteraction).where(AIInteraction.id == interaction.id))
            policy.daily_token_budget = previous_budget
            policy.enabled = previous_enabled
            await db.commit()
