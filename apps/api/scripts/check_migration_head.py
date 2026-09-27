"""Fail unless the configured database is at every Alembic migration head."""

from alembic import command
from alembic.config import Config


def main() -> None:
    config = Config("alembic.ini")
    command.current(config, check_heads=True)
    print("Migration head check passed.")


if __name__ == "__main__":
    main()
