# -*- coding: utf-8 -*-
"""Write-path smoke: insert + upsert via SQLAlchemy on SQLite file."""
from __future__ import annotations

import os
from pathlib import Path

import models
from infrastructure.db import dispose_engine, init_engine


def _restore_default_pytest_engine() -> None:
    p = Path(__file__).resolve().parents[1] / ".pytest_runtime_default.sqlite3"
    url = f"sqlite:///{p.resolve().as_posix()}"
    os.environ["DATABASE_URL"] = url
    models.DB_PATH = str(p)
    dispose_engine()
    init_engine(url)
    models.init_db()


def test_sa_insert_upsert_same_db(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "w.db"
    path_str = str(db_file)
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setattr(models, "DB_PATH", path_str)
    monkeypatch.setenv("DATABASE_URL", url)
    dispose_engine()
    init_engine(url)
    models.init_db()
    base = {
        "uploader_name": "u1",
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
        "quarter": 0,
    }
    try:
        models.insert_entries([dict(base)])
        assert models.get_total_entries_count() == 1

        models.upsert_entries([{**base, "value": 222.0}])
        assert models.get_total_entries_count() == 1
        assert models.query_data_entries(limit=5, indicator="GDP")[0]["value"] == 222.0
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        _restore_default_pytest_engine()
