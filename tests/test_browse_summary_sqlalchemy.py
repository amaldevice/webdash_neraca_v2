# -*- coding: utf-8 -*-
"""browse helpers via SQLAlchemy on SQLite file."""
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
from models import browse


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

        filt = browse.get_filter_options()
        assert "GDP" in filt["indicators"]
        assert "A" in filt["uploaders"]
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        _restore_default_pytest_engine()
