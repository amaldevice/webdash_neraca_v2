# -*- coding: utf-8 -*-
"""SQLAlchemy read/write parity on a shared SQLite file."""
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


def test_sa_reads_same_sqlite_file(tmp_path, monkeypatch) -> None:
    db_file = tmp_path / "shared.db"
    path_str = str(db_file)
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setattr(models, "DB_PATH", path_str)
    monkeypatch.setenv("DATABASE_URL", url)
    dispose_engine()
    init_engine(url)
    models.init_db()
    try:
        assert models.insert_single_entry(
            uploader="Tester",
            version="v1",
            data_type="flow",
            time_period="monthly",
            period_date="2024-01",
            indicator="Inflasi",
            value=12.5,
        )
        models.insert_entries(
            [
                {
                    "uploader_name": "A",
                    "version": "v1",
                    "template_type": "manual",
                    "data_type": "flow",
                    "time_period": "monthly",
                    "indicator_name": "GDP",
                    "value": 100.0,
                    "year": 2024,
                    "month": 2,
                    "quarter": None,
                },
            ]
        )

        sa_rows = models.query_data_entries(limit=10)
        sa_count = models.get_total_entries_count()
        assert sa_count == 2
        assert len(sa_rows) == 2

        sa_min = models.query_data_entries(limit=10, value_min=50.0)
        assert len(sa_min) == 1
        assert sa_min[0]["value"] == 100.0

        sa_by_id = {r["id"]: r for r in sa_rows}
        for eid, srow in sa_by_id.items():
            assert srow["indicator_name"] in ("Inflasi", "GDP")
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        _restore_default_pytest_engine()


def test_preview_duplicates_batches_on_sa(tmp_path, monkeypatch) -> None:
    from models.queries import preview_duplicates_batches

    db_file = tmp_path / "dup.db"
    path_str = str(db_file)
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setattr(models, "DB_PATH", path_str)
    monkeypatch.setenv("DATABASE_URL", url)
    dispose_engine()
    init_engine(url)
    models.init_db()
    entry = {
        "uploader_name": "u1",
        "version": "v1",
        "template_type": "manual",
        "data_type": "flow",
        "time_period": "monthly",
        "indicator_name": "GDP",
        "value": 42.0,
        "unit": None,
        "region_code": None,
        "year": 2024,
        "month": 5,
        "quarter": None,
        "dataset_code": "",
    }
    try:
        models.insert_entries([entry])
        keys = [("GDP", 2024, 5, None, "")]
        dups = preview_duplicates_batches(keys)
        assert len(dups) == 1
        assert dups[0]["value"] == 42.0
        assert dups[0]["indicator_name"] == "GDP"
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        _restore_default_pytest_engine()


def test_fetch_series_for_comparison_on_sa(tmp_path, monkeypatch) -> None:
    from models.queries import fetch_series_for_comparison

    db_file = tmp_path / "series.db"
    path_str = str(db_file)
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setattr(models, "DB_PATH", path_str)
    monkeypatch.setenv("DATABASE_URL", url)
    dispose_engine()
    init_engine(url)
    models.init_db()
    rows_payload = [
        {
            "uploader_name": "u1",
            "version": "v1",
            "template_type": "manual",
            "data_type": "flow",
            "time_period": "monthly",
            "indicator_name": "GDP",
            "value": 1.0,
            "unit": None,
            "region_code": None,
            "year": 2024,
            "month": 1,
            "quarter": None,
        },
        {
            "uploader_name": "u1",
            "version": "v1",
            "template_type": "manual",
            "data_type": "flow",
            "time_period": "monthly",
            "indicator_name": "GDP",
            "value": 2.0,
            "unit": None,
            "region_code": None,
            "year": 2024,
            "month": 6,
            "quarter": None,
        },
        {
            "uploader_name": "u1",
            "version": "v1",
            "template_type": "manual",
            "data_type": "flow",
            "time_period": "monthly",
            "indicator_name": "GDP",
            "value": 99.0,
            "unit": None,
            "region_code": None,
            "year": 2023,
            "month": 12,
            "quarter": None,
        },
    ]
    try:
        models.insert_entries(rows_payload)
        series = fetch_series_for_comparison(
            "GDP", "2024", period_start="2024-02", period_end="2024-06"
        )
        assert len(series) == 1
        assert series[0]["value"] == 2.0
        assert series[0]["month"] == 6
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        _restore_default_pytest_engine()
