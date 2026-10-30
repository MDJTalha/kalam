"""Shared pytest bootstrap for the API test suite."""

import os
import sys
from pathlib import Path

# Integration tests must opt into a dedicated PostgreSQL test database. Do not
# inherit the developer .env database or silently run against SQLite.
os.environ["APP_ENV"] = "test"
test_database_url = os.environ.get("KALAM_TEST_DATABASE_URL", "")
if not test_database_url.lower().startswith(("postgresql://", "postgresql+asyncpg://")):
    raise RuntimeError(
        "API tests require KALAM_TEST_DATABASE_URL explicitly pointing to an isolated PostgreSQL test database."
    )
os.environ["DATABASE_URL"] = test_database_url

# TestClient can execute requests on a different event loop than fixture setup.
# Keep NullPool for tests while local development servers use the QueuePool path.
os.environ.setdefault("DATABASE_POOL_MODE", "null")
os.environ.setdefault("AI_ENABLED", "true")

API_ROOT = Path(__file__).parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
