import asyncio
import json
import os
import time

import httpx

BASE = os.getenv("PERF_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_PREFIX = os.getenv("PERF_API_PREFIX", "/api/v1").rstrip("/")
LOGIN_PATH = os.getenv("PERF_LOGIN_PATH", f"{API_PREFIX}/auth/login")
TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
COOKIE = "corp_lms_session"

PROFILES = [
    {"path": f"{API_PREFIX}/health", "total": 100, "concurrency": 10, "p95_limit_ms": 750},
    {"path": f"{API_PREFIX}/health/ready", "total": 30, "concurrency": 5, "p95_limit_ms": 1000},
    {"path": f"{API_PREFIX}/auth/me", "total": 100, "concurrency": 10, "p95_limit_ms": 1500},
]


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * p))))
    return round(ordered[index], 2)


async def exercise(
    client: httpx.AsyncClient,
    path: str,
    total: int,
    concurrency: int,
    p95_limit_ms: int,
) -> dict:
    semaphore = asyncio.Semaphore(concurrency)
    durations: list[float] = []
    failures: list[str] = []

    async def one() -> None:
        async with semaphore:
            started = time.perf_counter()
            try:
                response = await client.get(path)
                durations.append((time.perf_counter() - started) * 1000)
                if response.status_code != 200:
                    failures.append(str(response.status_code))
            except httpx.HTTPError as exc:
                durations.append((time.perf_counter() - started) * 1000)
                failures.append(type(exc).__name__)

    await asyncio.gather(*(one() for _ in range(total)))
    return {
        "path": path,
        "requests": total,
        "concurrency": concurrency,
        "failures": len(failures),
        "p50_ms": percentile(durations, 0.50),
        "p95_ms": percentile(durations, 0.95),
        "max_ms": round(max(durations), 2),
        "p95_limit_ms": p95_limit_ms,
    }


async def main() -> None:
    timeout = httpx.Timeout(15)
    async with httpx.AsyncClient(base_url=BASE, timeout=timeout) as client:
        login = await client.post(
            LOGIN_PATH,
            json={"tenant_slug": TENANT, **ADMIN},
        )
        login.raise_for_status()
        session = client.cookies.get(COOKIE)
        if not session:
            raise RuntimeError("Login did not issue a session cookie")
        # Local HTTP release-candidate runs may receive a production Secure cookie.
        # Supply the captured token explicitly so the smoke still exercises authenticated server behavior.
        client.headers["Cookie"] = f"{COOKIE}={session}"
        results = [await exercise(client, **profile) for profile in PROFILES]

    print(json.dumps(results, indent=2))
    failed = [
        result
        for result in results
        if result["failures"] or result["p95_ms"] > result["p95_limit_ms"]
    ]
    if failed:
        raise SystemExit("Performance smoke gate failed: " + json.dumps(failed))


if __name__ == "__main__":
    asyncio.run(main())
