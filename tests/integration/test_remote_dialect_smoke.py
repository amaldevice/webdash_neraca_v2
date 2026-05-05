# -*- coding: utf-8 -*-
"""Smoke tests for SQLAlchemy write/read against MySQL or PostgreSQL (CI services).

Local: skip unless ``DATABASE_URL`` is set to a non-sqlite DSN and schema exists
(``python -m alembic upgrade head``).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

import models
from infrastructure.db import dispose_engine, init_engine

REPO_ROOT = Path(__file__).resolve().parents[2]


def _remote_database_url() -> str | None:
    raw = (os.environ.get("DATABASE_URL") or "").strip()
    if not raw or raw.startswith("sqlite"):
        return None
    return raw


pytestmark = pytest.mark.skipif(
    _remote_database_url() is None,
    reason="Set DATABASE_URL to mysql+ or postgresql+ (see README integration section)",
)


@pytest.fixture(scope="module")
def remote_engine_module(tmp_path_factory: pytest.TempPathFactory) -> str:
    url = _remote_database_url()
    assert url is not None
    dispose_engine()
    mp = MonkeyPatch()
    side = tmp_path_factory.mktemp("sqlite_sidecar") / "legacy.db"
    mp.setattr(models, "DB_PATH", str(side))
    models.init_db()
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(REPO_ROOT),
        env=env,
        check=True,
    )
    init_engine(url)
    assert models.clear_all_data() is True
    yield url
    dispose_engine()
    mp.undo()


@pytest.mark.usefixtures("remote_engine_module")
def test_insert_entries_and_count() -> None:
    assert models.clear_all_data() is True
    models.insert_entries(
        [
            {
                "uploader_name": "ci_u1",
                "version": "v1",
                "template_type": "manual",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": "GDP",
                "value": 100.0,
                "unit": None,
                "region_code": None,
                "year": 2024,
                "month": 1,
                "quarter": None,
            },
        ]
    )
    assert models.get_total_entries_count() == 1
    rows = models.query_data_entries(limit=5, indicator="GDP")
    assert len(rows) == 1
    assert rows[0]["value"] == 100.0


@pytest.mark.usefixtures("remote_engine_module")
def test_upsert_overwrites_same_unique_key() -> None:
    models.clear_all_data()
    base = {
        "uploader_name": "ci_u2",
        "version": "v1",
        "template_type": "manual",
        "data_type": "flow",
        "time_period": "monthly",
        "indicator_name": "CPI",
        "value": 50.0,
        "unit": None,
        "region_code": None,
        "year": 2024,
        "month": 3,
        "quarter": None,
    }
    models.insert_entries([dict(base)])
    models.upsert_entries([{**base, "value": 77.0}])
    assert models.get_total_entries_count() == 1
    rows = models.query_data_entries(limit=5, indicator="CPI")
    assert rows[0]["value"] == 77.0
