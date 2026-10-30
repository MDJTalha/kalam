import asyncio
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool, Pool, StaticPool

from app.core.config import settings

if settings.database_pool_mode == "null":
    pool_class: type[Pool] = NullPool
else:
    pool_class = AsyncAdaptedQueuePool


async def _postgres_is_available(url: str) -> bool:
    engine = create_async_engine(url, pool_pre_ping=True, future=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except (SQLAlchemyError, OSError, TimeoutError):
        return False
    finally:
        await engine.dispose()


def _run_postgres_availability_check(url: str) -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_postgres_is_available(url))

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(_postgres_is_available(url))).result()


def _build_sqlite_engine() -> AsyncEngine:
    database_url = settings.database_url
    parsed = make_url(database_url)
    sqlite_path = Path("./data/kalam-local.sqlite3")
    if parsed.drivername.startswith("sqlite") and parsed.database:
        sqlite_path = Path(parsed.database)
    if not sqlite_path.is_absolute():
        sqlite_path = (Path(__file__).resolve().parents[2] / sqlite_path).resolve()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(
        f"sqlite+aiosqlite:///{sqlite_path}",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        future=True,
    )


def _build_postgres_engine(database_url: str) -> AsyncEngine:
    if settings.app_env == "production":
        return create_async_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_recycle=1800,
        )

    parsed = make_url(database_url)
    local_dev_db = parsed.host in {"localhost", "127.0.0.1", "::1", None}
    connect_args = {"ssl": False} if local_dev_db and parsed.drivername.startswith("postgresql") else {}
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
    return create_async_engine(database_url, **pool_kwargs)


def _build_engine() -> AsyncEngine:
    database_url = settings.database_url
    parsed = make_url(database_url)
    if parsed.drivername.startswith("sqlite"):
        if settings.app_env.lower() in {"test", "ci"}:
            raise RuntimeError(
                "APP_ENV=test/ci requires an explicit PostgreSQL DATABASE_URL; refusing SQLite fallback."
            )
        return _build_sqlite_engine()

    if settings.app_env.lower() in {"development", "test", "ci"}:
        if _run_postgres_availability_check(database_url):
            return _build_postgres_engine(database_url)
        if settings.app_env.lower() in {"test", "ci"}:
            raise RuntimeError(
                "PostgreSQL is unavailable for APP_ENV=test/ci; refusing SQLite fallback."
            )
        return _build_sqlite_engine()

    return _build_postgres_engine(database_url)


engine: AsyncEngine = _build_engine()
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
