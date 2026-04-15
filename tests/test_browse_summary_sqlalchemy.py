# -*- coding: utf-8 -*-
"""Parity: browse + summary_store via SQLAlchemy vs legacy (same SQLite file)."""
from __future__ import annotations

import models
from infrastructure.db import dispose_engine, init_engine
from models import browse, summary_store


def test_browse_and_summary_sa_match_legacy(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "bs.db"
    path_str = str(db_file)
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setattr(models, "DB_PATH", path_str)
    monkeypatch.setenv("DATABASE_URL", url)
    models.init_db()
    init_engine(url)
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

        meta_sa = browse.get_latest_metadata()
        years_sa = browse.get_distinct_years()
        cards_sa = browse.get_aggregated_cards(limit=5)
        filt_sa = browse.get_filter_options()
        ind_sa = browse.get_unique_indicators()

        summary_store.save_aggregated_summary({"k": "v"})
        loaded_sa = summary_store.load_cached_summary()

        monkeypatch.delenv("DATABASE_URL", raising=False)
        dispose_engine()

        meta_leg = browse.get_latest_metadata()
        years_leg = browse.get_distinct_years()
        cards_leg = browse.get_aggregated_cards(limit=5)
        filt_leg = browse.get_filter_options()
        ind_leg = browse.get_unique_indicators()
        loaded_leg = summary_store.load_cached_summary()

        assert meta_sa["uploader"] == meta_leg["uploader"]
        assert meta_sa["version"] == meta_leg["version"]
        assert years_sa == years_leg == [2024]
        assert len(cards_sa) == len(cards_leg)
        assert filt_sa == filt_leg
        assert ind_sa == ind_leg == ["GDP"]
        assert loaded_sa == loaded_leg == {"k": "v"}
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        dispose_engine()
