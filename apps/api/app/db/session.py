from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool, Pool

from app.core.config import settings


if settings.database_pool_mode == "null":
    pool_class: type[Pool] = NullPool
else:
    pool_class = AsyncAdaptedQueuePool


if settings.app_env == "production":
    engine: AsyncEngine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_recycle=1800,
    )
else:
    # Tests explicitly select NullPool because TestClient may use a separate
    # event loop. Normal local development uses the async-safe queue pool.
    # The local Docker PostgreSQL endpoint is intentionally non-TLS; disable
    # asyncpg SSL negotiation only for localhost development connections.
    local_dev_db = make_url(settings.database_url).host in {"localhost", "127.0.0.1", "::1"}
    connect_args = {"ssl": False} if local_dev_db else {}
    pool_kwargs: dict[str, object] = {
        "poolclass": pool_class,
        "pool_pre_ping": True,
        "connect_args": connect_args,
    }
    if pool_class is not NullPool:
        pool_kwargs.update(
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_recycle=1800,
        )
    engine = create_async_engine(settings.database_url, **pool_kwargs)

SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
