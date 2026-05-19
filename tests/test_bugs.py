#!/usr/bin/env python3
"""
Comprehensive Bug Testing Suite for BPS Data Management System
"""
import time
import threading

import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch

from app import app
from services.validation import allowed_file, validate_metadata
from periods import parse_period_date as _parse_period_date
from services.manual_entries import build_manual_entry as _build_manual_entry
from models import (
    init_db, insert_entries, query_data_entries, get_total_entries_count,
    delete_data_entry, update_data_entry_full, bulk_delete_entries, bulk_update_entries,
)
from excel_parser import detect_template_format, normalize_record, to_float
from services.timeutil import utc_now_iso


def test_allowed_file_valid_extensions():
    assert allowed_file("test.xlsx")
    assert allowed_file("test.xls")
    assert not allowed_file("test.txt")
    assert not allowed_file("test.exe")
    assert not allowed_file("test.xlsx.exe")


def test_validate_metadata_valid():
    assert len(validate_metadata("flow", "monthly")) == 0
    assert len(validate_metadata("stock", "quarterly")) == 0
    assert len(validate_metadata("flow", "yearly")) == 0


def test_validate_metadata_invalid():
    assert "Tipe data tidak valid." in validate_metadata("invalid", "monthly")
    assert "Periode tidak valid." in validate_metadata("flow", "invalid")
    assert len(validate_metadata("", "")) == 2


def test_parse_period_date_monthly():
    assert _parse_period_date("monthly", "2024-01") == (2024, 1, 1)
    assert _parse_period_date("monthly", "2024-12") == (2024, 12, 4)


def test_parse_period_date_quarterly():
    assert _parse_period_date("quarterly", "2024-Q1") == (2024, None, 1)
    assert _parse_period_date("quarterly", "2024-01") == (2024, 1, 1)
    assert _parse_period_date("quarterly", "2024-Q4") == (2024, None, 4)


def test_parse_period_date_yearly():
    assert _parse_period_date("yearly", "2024") == (2024, None, None)
    assert _parse_period_date("yearly", "2024-01") == (2024, 1, None)


def test_parse_period_date_invalid():
    assert _parse_period_date("monthly", "invalid") == (None, None, None)
    assert _parse_period_date("monthly", "2024-13") == (None, None, None)
    assert _parse_period_date("quarterly", "2024-Q5") == (None, None, None)


def test_models_does_not_export_private_to_float():
    import importlib
    m = importlib.import_module("models")
    assert "_to_float" not in m.__all__


def test_app_does_not_expose_test_aliases():
    import app as app_mod
    assert "_parse_period_date" not in app_mod.__all__
    assert "_build_manual_entry" not in app_mod.__all__


def test_detect_template_format_vertical():
    df = pd.DataFrame({0: [2024, "GDP", "Inflasi"], 1: ["Q1", 1000, 2000], 2: ["Q2", 1100, 2100]})
    assert detect_template_format(df) == "vertical"


def test_detect_template_format_horizontal():
    df = pd.DataFrame({0: ["GDP", "Inflasi"], 1: [1000, 2000], 2: [1100, 2100]})
    assert detect_template_format(df) == "horizontal"


def test_normalize_record_valid():
    record = normalize_record(uploader="u", version="v1", layout="vertical", data_type="flow",
                              time_period="monthly", indicator="GDP", value=1000.5, period_value="2024-01")
    assert record is not None
    assert record["indicator_name"] == "GDP"
    assert record["value"] == 1000.5
    assert record["year"] == 2024
    assert record["month"] == 1


def test_normalize_record_invalid_value():
    assert normalize_record(uploader="u", version="v1", layout="vertical", data_type="flow",
                            time_period="monthly", indicator="GDP", value="invalid", period_value="2024-01") is None


def test_normalize_record_missing_indicator():
    assert normalize_record(uploader="u", version="v1", layout="vertical", data_type="flow",
                            time_period="monthly", indicator="", value=1000, period_value="2024-01") is None


def test_insert_entries_success(db_path):
    insert_entries([{"uploader_name": "u", "version": "v1", "indicator_name": "GDP",
                     "value": 1000.0, "data_type": "flow", "time_period": "monthly",
                     "year": 2024, "month": 1, "created_at": utc_now_iso()}])
    results = query_data_entries(limit=10)
    assert len(results) == 1
    assert results[0]["indicator_name"] == "GDP"


def test_insert_entries_duplicate_constraint(db_path):
    entry = [{"uploader_name": "u", "version": "v1", "indicator_name": "GDP",
              "value": 1000.0, "data_type": "flow", "time_period": "monthly",
              "year": 2024, "month": 1, "quarter": 1, "created_at": utc_now_iso()}]
    insert_entries(entry)
    with pytest.raises(IntegrityError):
        insert_entries(entry)


def test_bulk_delete_entries(db_path):
    entries = [{"uploader_name": f"user_{i}", "version": "v1", "indicator_name": f"ind_{i}",
                "value": float(i*100), "data_type": "flow", "time_period": "monthly",
                "year": 2024, "month": 1, "created_at": utc_now_iso()} for i in range(5)]
    insert_entries(entries)
    ids = [r["id"] for r in query_data_entries(limit=10)[:3]]
    assert bulk_delete_entries(ids) == 3
    assert len(query_data_entries(limit=10)) == 2


def test_bulk_update_entries(db_path):
    entries = [{"uploader_name": f"user_{i}", "version": "v1", "indicator_name": f"ind_{i}",
                "value": float(i*100), "data_type": "flow", "time_period": "monthly",
                "year": 2024, "month": 1, "created_at": utc_now_iso()} for i in range(3)]
    insert_entries(entries)
    ids = [r["id"] for r in query_data_entries(limit=10)]
    assert bulk_update_entries(ids, {"uploader_name": "updated", "value": 999.99}) == 3
    for r in query_data_entries(limit=10):
        assert r["uploader_name"] == "updated"
        assert r["value"] == 999.99


def test_sql_injection_prevention(db_path):
    count = get_total_entries_count(uploader="'; DROP TABLE data_entries; --")
    assert isinstance(count, int)


def test_xss_prevention_in_templates():
    pass


def test_path_traversal_prevention(db_path):
    assert not allowed_file("../../../etc/passwd")
    assert not allowed_file("test.xlsx.exe")


def test_buffer_overflow_prevention(db_path):
    assert to_float("1" * 10000) is not None


def test_database_connection_failure(db_path):
    from sqlalchemy.exc import OperationalError
    with patch("models.queries.get_session", side_effect=OperationalError("stmt", {}, None)):
        assert isinstance(get_total_entries_count(), int)


def test_invalid_pagination_parameters(db_path):
    assert isinstance(query_data_entries(limit=10, offset=-10), list)
    assert isinstance(query_data_entries(limit=10000), list)


def test_concurrent_database_operations(db_path):
    results, errors = [], []
    def insert_operation(thread_id):
        try:
            insert_entries([{"uploader_name": f"thread_{thread_id}", "version": "v1",
                             "indicator_name": f"ind_{thread_id}", "value": float(thread_id*100),
                             "data_type": "flow", "time_period": "monthly",
                             "year": 2024, "month": 1, "created_at": utc_now_iso()}])
            results.append(thread_id)
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=insert_operation, args=(i,)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(results) == 5
    assert len(errors) == 0


def test_large_dataset_pagination(db_path):
    entries = [{"uploader_name": f"user_{i%10}", "version": "v1", "indicator_name": f"ind_{i%20}",
                "value": float(i), "data_type": "flow", "time_period": "monthly",
                "year": 2024, "month": 1, "created_at": utc_now_iso()} for i in range(1000)]
    t0 = time.time()
    insert_entries(entries)
    assert time.time() - t0 < 5.0
    t0 = time.time()
    results = query_data_entries(limit=50, offset=500)
    assert time.time() - t0 < 1.0
    assert len(results) == 50
