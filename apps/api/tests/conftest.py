"""Shared pytest bootstrap for the API test suite."""

import os
from pathlib import Path
import sys

# TestClient can execute requests on a different event loop than fixture setup.
# Keep NullPool for tests while local development servers use the QueuePool path.
os.environ.setdefault("DATABASE_POOL_MODE", "null")
os.environ.setdefault("AI_ENABLED", "true")

API_ROOT = Path(__file__).parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
