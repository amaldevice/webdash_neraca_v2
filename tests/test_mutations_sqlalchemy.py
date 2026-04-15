# -*- coding: utf-8 -*-
"""Write-path parity: insert + upsert via SQLAlchemy vs legacy sqlite3 (same file)."""
from __future__ import annotations

import models
from infrastructure.db import dispose_engine, init_engine


def test_sa_insert_upsert_match_legacy_same_db(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "w.db"
    path_str = str(db_file)
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setattr(models, "DB_PATH", path_str)
    monkeypatch.setenv("DATABASE_URL", url)
    models.init_db()
    init_engine(url)
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

        monkeypatch.delenv("DATABASE_URL", raising=False)
        dispose_engine()

        assert models.get_total_entries_count() == 1
        assert models.query_data_entries(limit=5, indicator="GDP")[0]["value"] == 222.0
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        dispose_engine()
