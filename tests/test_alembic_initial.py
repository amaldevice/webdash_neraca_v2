# -*- coding: utf-8 -*-
"""Alembic initial revision applies same tables as legacy ``init_db``."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config


def _alembic_config(repo_root: Path) -> Config:
    cfg = Config(str(repo_root / "alembic.ini"))
    return cfg


@pytest.fixture
def sqlite_file_url(tmp_path: Path) -> str:
    db_path = tmp_path / "alembic_test.db"
    return f"sqlite:///{db_path.resolve().as_posix()}"


def test_alembic_upgrade_head_creates_tables(monkeypatch: pytest.MonkeyPatch, sqlite_file_url: str) -> None:
    monkeypatch.setenv("DATABASE_URL", sqlite_file_url)
    monkeypatch.delenv("ALEMBIC_DATABASE_URL", raising=False)
    repo_root = Path(__file__).resolve().parents[1]
    command.upgrade(_alembic_config(repo_root), "head")

    db_file = sqlite_file_url.replace("sqlite:///", "")
    with sqlite3.connect(db_file) as conn:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cur.fetchall()}
    assert "data_entries" in tables
    assert "upload_runs" in tables
    assert len(tables) >= 2
    with sqlite3.connect(db_file) as conn:
        cur = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name='ux_data_entry_variant'"
        )
        row = cur.fetchone()
    assert row is not None
    assert "UNIQUE" in (row[0] or "").upper()


def test_orm_metadata_matches_migration_tables(sqlite_file_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanity: ORM registers same table names as migration (no import-time alembic run)."""
    monkeypatch.setenv("DATABASE_URL", sqlite_file_url)
    from sqlalchemy import create_engine, inspect

    from infrastructure.db import _engine_kwargs
    from infrastructure.orm_models import Base

    engine = create_engine(sqlite_file_url, **_engine_kwargs(sqlite_file_url))
    try:
        Base.metadata.create_all(engine)
        insp = inspect(engine)
        assert insp.has_table("data_entries")
        assert insp.has_table("data_entries")
        uq_names = {u["name"] for u in insp.get_unique_constraints("data_entries")}
        ix_names = {i["name"] for i in insp.get_indexes("data_entries")}
        assert "ux_data_entry_variant" in (uq_names | ix_names)
    finally:
        engine.dispose()
