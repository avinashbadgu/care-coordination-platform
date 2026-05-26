"""Create all tables directly from SQLAlchemy metadata.

This is a developer convenience for the very first run before any Alembic
migrations exist. For real schema evolution use:

    alembic revision --autogenerate -m "init"
    alembic upgrade head
"""
from __future__ import annotations

from app.core.db import engine
from app.models import Base


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print(f"Created tables on {engine.url}")


if __name__ == "__main__":
    main()
