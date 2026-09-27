from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter()

_production_redis: Redis | None = (
    Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
    if settings.app_env == "production"
    else None
)


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "corplms-api"}


@router.get("/health/live", tags=["system"])
async def liveness() -> dict[str, str]:
    return {"status": "alive", "service": "corplms-api"}


@router.get("/health/ready", tags=["system"])
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    checks = {"database": "unknown", "redis": "unknown"}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ready"
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": {**checks, "database": "failed"}},
        ) from exc

    redis = _production_redis or Redis.from_url(
        settings.redis_url, socket_connect_timeout=2, socket_timeout=2
    )
    try:
        if not await redis.ping():
            raise RuntimeError("Redis ping returned false")
        checks["redis"] = "ready"
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": {**checks, "redis": "failed"}},
        ) from exc
    finally:
        if _production_redis is None:
            await redis.aclose()

    return {"status": "ready", **checks}
