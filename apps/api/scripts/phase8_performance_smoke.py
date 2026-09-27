import asyncio
import json
import os
import time

import httpx

BASE = os.getenv("PERF_BASE_URL", "http://127.0.0.1:8000")
TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}

PROFILES = [
    {"path": "/api/v1/health", "total": 100, "concurrency": 10, "p95_limit_ms": 750},
    {"path": "/api/v1/health/ready", "total": 30, "concurrency": 5, "p95_limit_ms": 1000},
    {"path": "/api/v1/auth/me", "total": 100, "concurrency": 10, "p95_limit_ms": 1500},
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
            "/api/v1/auth/login",
            json={"tenant_slug": TENANT, **ADMIN},
        )
        login.raise_for_status()
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
