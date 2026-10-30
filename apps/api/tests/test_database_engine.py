import asyncio

from app.db import session


def test_postgres_availability_check_runs_with_an_active_event_loop(monkeypatch) -> None:
    async def available(_url: str) -> bool:
        return True

    monkeypatch.setattr(session, "_postgres_is_available", available)

    async def check() -> bool:
        return session._run_postgres_availability_check("postgresql+asyncpg://test")

    assert asyncio.run(check()) is True
