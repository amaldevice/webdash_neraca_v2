from __future__ import annotations

import models


def test_insert_entries_increases_row_count(db_path):
    models.insert_entries(
        [
            {
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
                "quarter": None,
            },
            {
                "uploader_name": "u2",
                "version": "v1",
                "template_type": "manual",
                "data_type": "stock",
                "time_period": "quarterly",
                "indicator_name": "CPI",
                "value": 200.0,
                "unit": None,
                "region_code": None,
                "year": 2024,
                "month": None,
                "quarter": 2,
            },
        ]
    )
    assert models.get_total_entries_count() == 2


def test_delete_data_entry_reduces_row_count_by_one(db_path):
    models.insert_entries(
        [
            {
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
                "quarter": None,
            },
            {
                "uploader_name": "u2",
                "version": "v1",
                "template_type": "manual",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": "CPI",
                "value": 200.0,
                "unit": None,
                "region_code": None,
                "year": 2024,
                "month": 2,
                "quarter": None,
            },
        ]
    )
    rows = models.query_data_entries(limit=10)
    assert len(rows) == 2
    entry_id = str(rows[0]["id"])

    deleted = models.delete_data_entry(entry_id)
    assert deleted is True
    assert models.get_total_entries_count() == 1


def test_update_data_entry_keeps_row_count_and_changes_value(db_path):
    models.insert_entries(
        [
            {
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
                "month": 3,
                "quarter": None,
            },
        ]
    )
    row = models.query_data_entries(limit=10)[0]
    entry_id = str(row["id"])

    updated = models.update_data_entry(entry_id, 123.45)
    assert updated is True
    assert models.get_total_entries_count() == 1
    assert models.query_data_entries(limit=10)[0]["value"] == 123.45


def test_upsert_entries_overwrites_existing_row(db_path):
    # SQLite UNIQUE + ON CONFLICT ignore NULL key parts as distinct; keep all unique
    # index columns non-NULL so upsert targets one physical row.
    base_entry = {
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
    models.insert_entries([base_entry])

    updated_entry = {**base_entry, "value": 999.0, "time_period": "monthly"}
    models.upsert_entries([updated_entry])

    assert models.get_total_entries_count() == 1
    row = models.query_data_entries(limit=10, indicator="GDP")[0]
    assert row["value"] == 999.0
