# -*- coding: utf-8 -*-
"""Optional SQLAlchemy ``session`` injection on read/write model APIs (tests + tooling)."""
from __future__ import annotations

from unittest.mock import MagicMock

from sqlalchemy.orm import sessionmaker

from infrastructure.db import get_engine
from models import insert_entries, query_data_entries
from models.queries import get_total_entries_count


def test_get_total_entries_count_uses_injected_session():
    mock_sess = MagicMock()
    mock_sess.execute.return_value.scalar_one.return_value = 7
    assert get_total_entries_count(session=mock_sess) == 7
    mock_sess.execute.assert_called_once()


def test_insert_entries_with_explicit_session_commits(db_path):
    eng = get_engine()
    assert eng is not None
    factory = sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)
    entry = {
        "uploader_name": "Seam",
        "version": "v1",
        "template_type": "excel",
        "data_type": "flow",
        "time_period": "monthly",
        "indicator_name": "SeamInd",
        "value": 3.14,
        "unit": None,
        "region_code": None,
        "year": 2024,
        "month": 2,
        "quarter": 1,
        "dataset_code": "",
    }
    with factory() as s:
        insert_entries([entry], session=s)
    rows = query_data_entries(indicator="SeamInd", limit=5)
    assert any(r["indicator_name"] == "SeamInd" for r in rows)
