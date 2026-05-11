# -*- coding: utf-8 -*-
"""Unit tests for services.upload_parse."""
from __future__ import annotations

from unittest.mock import patch

from services.upload_parse import parse_and_validate_upload_payload


def test_parse_and_validate_sets_dataset_code_on_entries():
    row = {"indicator_name": "GDP", "year": 2024, "month": 1, "quarter": 1, "value": 1.0}
    payload = {"entries": [dict(row)], "warnings": ["sheet ok"]}
    with patch("services.upload_parse.parse_excel_payload", return_value=payload):
        out_payload, entries, warnings = parse_and_validate_upload_payload(
            "/tmp/f.xlsx",
            "U1",
            "v1",
            "flow",
            "monthly",
            dataset_slug="pinjaman",
        )
    assert out_payload is payload
    assert entries[0]["dataset_code"] == "pinjaman"
    assert warnings[0] == "sheet ok"


def test_parse_and_validate_appends_internal_file_duplicate_warning():
    dup_a = {"indicator_name": "GDP", "year": 2024, "month": 1, "quarter": 1, "value": 1.0}
    dup_b = {**dup_a, "value": 2.0}
    payload = {"entries": [dup_a, dup_b], "warnings": []}
    with patch("services.upload_parse.parse_excel_payload", return_value=payload):
        _, _, warnings = parse_and_validate_upload_payload(
            "/tmp/f.xlsx", "U1", "v1", "flow", "monthly", dataset_slug=None
        )
    assert len(warnings) == 1
    assert "duplikasi ekstra" in warnings[0]
