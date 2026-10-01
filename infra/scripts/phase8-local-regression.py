"""Run API regression in a disposable database without changing local demo data."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import asyncpg
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "apps" / "api"
sys.path.insert(0, str(API))
from app.core.config import settings  # noqa: E402


def scanner_ready(host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=8) as client:
        client.sendall(b"PING\n")
        if client.recv(100).strip() != b"PONG":
            raise RuntimeError("ClamAV did not answer PONG")

def run_step(label: str, args: list[str], env: dict[str, str]) -> None:
    print(f"[RUN] {label}", flush=True)
    subprocess.run([sys.executable, *args], cwd=API, env=env, check=True)
    print(f"[PASS] {label}", flush=True)


async def verify() -> None:
    url = make_url(settings.database_url)
    if url.get_backend_name() != "postgresql" or url.host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Verification requires a local PostgreSQL URL")
    name = "phase8_verify_" + uuid4().hex[:12]
    admin_url = url.set(drivername="postgresql", database="postgres")
    candidate_url = url.set(database=name)
    scanner_host = "127.0.0.1"
    scanner_port = int(os.getenv("PHASE8_SCAN_PORT", "55000"))
    scanner_ready(scanner_host, scanner_port)
    admin = await asyncpg.connect(dsn=admin_url.render_as_string(hide_password=False))
    created = False
    try:
        await admin.execute(f'CREATE DATABASE "{name}"')
        created = True
        with tempfile.TemporaryDirectory(prefix="phase8-uploads-") as uploads:
            env = os.environ.copy()
            env.update(DATABASE_URL=candidate_url.render_as_string(hide_password=False),
                       FILE_SCAN_PROVIDER="clamd", FILE_SCAN_HOST=scanner_host,
                       FILE_SCAN_PORT=str(scanner_port), FILE_STORAGE_ROOT=uploads,
                       STORAGE_ROOT=uploads, SAAS_OPS_TENANT_SLUG="kalam",
                       ALLOWED_HOSTS="localhost,127.0.0.1")
            redis = urlsplit(settings.redis_url)
            env["REDIS_URL"] = urlunsplit(redis._replace(path="/15"))
            python = Path(sys.executable)
            alembic = python.with_name("alembic.exe")
            print(f"Isolated database: {name}; scanner: {scanner_host}:{scanner_port}", flush=True)
            subprocess.run([str(alembic), "upgrade", "head"], cwd=API, env=env, check=True)
            run_step("demo seed", ["scripts/seed.py"], env)
            run_step("SaaS operator bootstrap", ["scripts/bootstrap_saas_ops.py"], env)
            run_step("full API suite", ["-m", "pytest", "tests", "-q"], env)
    finally:
        if created:
            await admin.execute(f'DROP DATABASE "{name}" WITH (FORCE)')
            print(f"Removed isolated database: {name}", flush=True)
        await admin.close()


if __name__ == "__main__":
    try:
        asyncio.run(verify())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
