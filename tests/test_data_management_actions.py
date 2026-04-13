# -*- coding: utf-8 -*-
"""Unit tests for CRUD POST handler (no HTTP)."""
from __future__ import annotations

from contextlib import closing

from werkzeug.datastructures import ImmutableMultiDict

import models
from services.data_management_actions import apply_data_management_post


def test_apply_delete_single_returns_success_message(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    models.insert_entries(
        [
            {
                "uploader_name": "u1",
                "version": "v1",
                "template_type": "manual",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": "GDP",
                "value": 1.0,
                "year": 2024,
                "month": 1,
                "quarter": None,
            }
        ]
    )
    with closing(models.get_conn()) as conn:
        row = conn.execute("SELECT id FROM data_entries LIMIT 1").fetchone()
        eid = str(row[0])

    form = ImmutableMultiDict([("action", "delete_single"), ("entry_id", eid)])
    msgs = apply_data_management_post(
        form,
        data_type="",
        time_period="",
        uploader="",
        indicator="",
        period_start=None,
        period_end=None,
        value_min=None,
        value_max=None,
    )
    assert msgs == [("Data berhasil dihapus.", "success")]
    assert models.get_total_entries_count() == 0


def test_apply_bulk_update_invalid_value_returns_error(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    models.insert_entries(
        [
            {
                "uploader_name": "u1",
                "version": "v1",
                "template_type": "manual",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": "GDPX",
                "value": 1.0,
                "year": 2024,
                "month": 2,
                "quarter": None,
            }
        ]
    )
    with closing(models.get_conn()) as conn:
        row = conn.execute("SELECT id FROM data_entries LIMIT 1").fetchone()
        eid = str(row[0])

    form = ImmutableMultiDict(
        [
            ("action", "bulk_update"),
            ("selected_ids[]", eid),
            ("bulk_update_value", "not-a-number"),
        ]
    )
    msgs = apply_data_management_post(
        form,
        data_type="",
        time_period="",
        uploader="",
        indicator="",
        period_start=None,
        period_end=None,
        value_min=None,
        value_max=None,
    )
    assert msgs == [("Nilai harus berupa angka.", "error")]


def test_apply_bulk_delete_action_removes_multiple_rows(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    models.insert_entries(
        [
            {
                "uploader_name": "u1",
                "version": "v1",
                "template_type": "manual",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": "GDPX",
                "value": 1.0,
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
                "indicator_name": "GDPY",
                "value": 2.0,
                "year": 2024,
                "month": 2,
                "quarter": None,
            },
        ]
    )
    with closing(models.get_conn()) as conn:
        rows = conn.execute("SELECT id FROM data_entries ORDER BY month").fetchall()
        ids = [str(row[0]) for row in rows]

    form = ImmutableMultiDict(
        [
            ("action", "bulk_delete"),
            ("selected_ids[]", ids[0]),
            ("selected_ids[]", ids[1]),
        ]
    )
    msgs = apply_data_management_post(
        form,
        data_type="",
        time_period="",
        uploader="",
        indicator="",
        period_start=None,
        period_end=None,
        value_min=None,
        value_max=None,
    )
    assert ("2 data berhasil dihapus.", "success") in msgs
    assert models.get_total_entries_count() == 0


def test_apply_insert_action_adds_data_entry(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()

    form = ImmutableMultiDict(
        [
            ("action", "insert"),
            ("insert_uploader", "admin"),
            ("insert_version", "v1"),
            ("insert_data_type", "flow"),
            ("insert_time_period", "monthly"),
            ("insert_period_date", "2024-01"),
            ("insert_indicator", "Inflasi"),
            ("insert_value", "123.45"),
        ]
    )
    msgs = apply_data_management_post(
        form,
        data_type="",
        time_period="",
        uploader="",
        indicator="",
        period_start=None,
        period_end=None,
        value_min=None,
        value_max=None,
    )
    assert ("Data baru berhasil ditambahkan.", "success") in msgs
    assert models.get_total_entries_count() == 1


def test_apply_update_data_entry_path_updates_value(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    models.insert_entries(
        [
            {
                "uploader_name": "u1",
                "version": "v1",
                "template_type": "manual",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": "Inflasi",
                "value": 12.0,
                "year": 2024,
                "month": 1,
                "quarter": None,
            }
        ]
    )
    row = models.query_data_entries(limit=1)[0]
    entry_id = str(row["id"])
    updated = models.update_data_entry(entry_id, 42.0)
    assert updated is True
    assert models.query_data_entries(limit=1)[0]["value"] == 42.0


def test_apply_update_action_with_invalid_value_returns_validation_error(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    models.insert_entries(
        [
            {
                "uploader_name": "u1",
                "version": "v1",
                "template_type": "manual",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": "Inflasi",
                "value": 12.0,
                "year": 2024,
                "month": 1,
                "quarter": None,
            }
        ]
    )
    row = models.query_data_entries(limit=1)[0]
    entry_id = str(row["id"])

    form = ImmutableMultiDict(
        [
            ("action", "update"),
            ("entry_id", entry_id),
            ("update_uploader", "u1"),
            ("update_version", "v1"),
            ("update_indicator", "Inflasi"),
            ("update_value", "invalid-number"),
            ("update_data_type", "flow"),
            ("update_time_period", "monthly"),
        ]
    )

    msgs = apply_data_management_post(
        form,
        data_type="",
        time_period="",
        uploader="",
        indicator="",
        period_start=None,
        period_end=None,
        value_min=None,
        value_max=None,
    )
    assert msgs == [("Nilai harus berupa angka.", "error")]


def test_apply_delete_by_filter_with_value_range_respects_bounds(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    models.insert_entries(
        [
            {
                "uploader_name": "u1",
                "version": "v1",
                "template_type": "manual",
                "data_type": "flow",
                "time_period": "monthly",
                "indicator_name": "GDP",
                "value": 10.0,
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
                "indicator_name": "GDP",
                "value": 200.0,
                "year": 2024,
                "month": 2,
                "quarter": None,
            },
        ]
    )

    form = ImmutableMultiDict([("action", "delete_by_filter")])
    msgs = apply_data_management_post(
        form,
        data_type="flow",
        time_period="monthly",
        uploader="",
        indicator="GDP",
        period_start=None,
        period_end=None,
        value_min=50.0,
        value_max=150.0,
    )

    assert ("1 data berhasil dihapus berdasarkan filter.", "success") in msgs
    assert models.get_total_entries_count() == 1
