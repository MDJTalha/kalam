import sys
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


API_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(API_ROOT))
MODULE_PATH = Path(__file__).parents[2] / "worker" / "report_scheduler.py"
SPEC = spec_from_file_location("corplms_report_scheduler", MODULE_PATH)
MODULE = module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_next_run_monthly_clamps_end_of_month():
    now = datetime(2026, 1, 31, 9, 30, tzinfo=timezone.utc)
    assert MODULE._next_run(now, "monthly") == datetime(2026, 2, 28, 9, 30, tzinfo=timezone.utc)


def test_next_run_monthly_preserves_leap_day_when_target_allows_it():
    now = datetime(2028, 1, 31, 9, 30, tzinfo=timezone.utc)
    assert MODULE._next_run(now, "monthly") == datetime(2028, 2, 29, 9, 30, tzinfo=timezone.utc)


def test_next_run_daily_and_weekly_are_deterministic():
    now = datetime(2026, 9, 25, 9, 30, tzinfo=timezone.utc)
    assert MODULE._next_run(now, "daily") == datetime(2026, 9, 26, 9, 30, tzinfo=timezone.utc)
    assert MODULE._next_run(now, "weekly") == datetime(2026, 10, 2, 9, 30, tzinfo=timezone.utc)
