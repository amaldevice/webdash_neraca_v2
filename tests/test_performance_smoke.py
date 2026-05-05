# -*- coding: utf-8 -*-
"""Performance smoke: bounded work completes within generous wall-clock limits (stdlib only)."""
from __future__ import annotations

import time

import models


def _insert_many(n: int) -> None:
    entries = []
    for i in range(n):
        entries.append(
            {
                "uploader_name": f"perf-u{i % 5}",
                "version": "v1",
                "template_type": "excel",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": f"PIND{i}",
                "value": float(i),
                "year": 2020 + (i // 50) % 10,
                "month": (i % 12) + 1,
                "quarter": None,
            }
        )
    models.insert_entries(entries)


def test_query_pagination_scales_under_one_second(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    _insert_many(400)

    t0 = time.perf_counter()
    rows = models.query_data_entries(limit=50, offset=100)
    elapsed = time.perf_counter() - t0

    assert len(rows) <= 50
    assert elapsed < 1.0


def test_total_count_scales_under_one_second(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    _insert_many(350)

    t0 = time.perf_counter()
    n = models.get_total_entries_count()
    elapsed = time.perf_counter() - t0

    assert n == 350
    assert elapsed < 1.0
