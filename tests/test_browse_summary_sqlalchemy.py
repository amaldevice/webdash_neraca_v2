# -*- coding: utf-8 -*-
"""browse + summary_store via SQLAlchemy on SQLite file."""
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
from models import browse, summary_store


def test_browse_and_summary_on_sa(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "bs.db"
    path_str = str(db_file)
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setattr(models, "DB_PATH", path_str)
    monkeypatch.setenv("DATABASE_URL", url)
    dispose_engine()
    init_engine(url)
    models.init_db()
    try:
        models.insert_entries(
            [
                {
                    "uploader_name": "A",
                    "version": "v1",
                    "template_type": "manual",
                    "data_type": "flow",
                    "time_period": "monthly",
                    "indicator_name": "GDP",
                    "value": 1.0,
                    "year": 2024,
                    "month": 1,
                    "quarter": 0,
                },
            ]
        )

        meta = browse.get_latest_metadata()
        years = browse.get_distinct_years()
        cards = browse.get_aggregated_cards(limit=5)
        filt = browse.get_filter_options()
        ind = browse.get_unique_indicators()

        summary_store.save_aggregated_summary({"k": "v"})
        loaded = summary_store.load_cached_summary()

        assert meta["uploader"] == "A"
        assert meta["version"] == "v1"
        assert years == [2024]
        assert len(cards) >= 1
        assert "GDP" in filt["indicators"]
        assert ind == ["GDP"]
        assert loaded == {"k": "v"}
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        _restore_default_pytest_engine()
