"""Test fixtures.

Each test gets a fresh in-memory SQLite database and a TestClient bound to
the FastAPI app. Storage is redirected to a per-test temp directory so file
uploads do not leak across tests.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Force a per-test SQLite file and storage dir before the app loads."""
    db_path = tmp_path / "test.sqlite"
    storage = tmp_path / "storage"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("STORAGE_DIR", str(storage))

    from app.core.config import get_settings

    get_settings.cache_clear()

    # Re-create engine/SessionLocal bound to the new URL. We replace the
    # module-level objects so any code that already imported them is updated.
    from app.core import db as db_module

    engine = create_engine(
        get_settings().resolved_database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
    db_module.engine = engine
    db_module.SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )

    from app.models import Base

    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    from app.core.db import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def patient_id(db) -> int:
    from app.models.patient import Patient

    p = Patient(full_name="Test Patient", timezone="UTC")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p.id
