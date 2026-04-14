# -*- coding: utf-8 -*-
"""Targeted tests for excel_parser (number parsing, detection, small real .xlsx)."""
from __future__ import annotations

import math

import pandas as pd
import pytest
from openpyxl import Workbook

from excel_parser import _parse_period, _to_float, detect_template_format, parse_excel_payload


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12,34", 12.34),
        ("1.234,56", 1234.56),
        ("1,234.56", 1234.56),
        ("  3,14  ", 3.14),
        ("", None),
        ("abc", None),
        (None, None),
        (42, 42.0),
        (12.5, 12.5),
    ],
)
def test_to_float_parsing(raw, expected):
    got = _to_float(raw)
    if expected is None:
        assert got is None
    elif isinstance(expected, float):
        assert got is not None and math.isclose(got, expected, rel_tol=0, abs_tol=1e-9)
    else:
        assert got == float(expected)


def test_detect_template_format_empty():
    df = pd.DataFrame()
    assert detect_template_format(df) == "horizontal"


def test_detect_template_format_vertical_signal():
    df = pd.DataFrame([["2024-01", 1], ["2024-02", 2]])
    assert detect_template_format(df) == "vertical"


def test_detect_template_format_horizontal_default():
    df = pd.DataFrame([["a", "b"], ["c", "d"]])
    assert detect_template_format(df) == "horizontal"


def test_parse_excel_payload_empty_workbook(tmp_path):
    path = tmp_path / "empty.xlsx"
    Workbook().save(path)
    payload = parse_excel_payload(str(path), "U", "v1", "flow", "monthly")
    assert payload["entries"] == []
    joined = " ".join(payload["warnings"])
    assert "kosong" in joined.lower()


def test_parse_excel_payload_horizontal_forced(tmp_path):
    """Minimal 2-row horizontal grid: header row with period columns + one data row."""
    path = tmp_path / "horizontal.xlsx"
    df = pd.DataFrame(
        [
            ["Indikator", pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
            ["GDP", 1.5, 2.5],
        ]
    )
    df.to_excel(path, index=False, header=False, engine="openpyxl")

    payload = parse_excel_payload(
        str(path),
        "Tester",
        "v-e2e",
        "flow",
        "monthly",
        layout_override="horizontal",
        preview_limit=5,
    )
    assert payload["layout"] == "horizontal"
    assert len(payload["entries"]) >= 1
    inds = {e["indicator_name"] for e in payload["entries"]}
    assert "GDP" in inds
    assert all(e["uploader_name"] == "Tester" and e["version"] == "v-e2e" for e in payload["entries"])
    assert len(payload["sample"]) <= 5


def test_parse_excel_payload_preview_sample_respects_limit(tmp_path):
    path = tmp_path / "multi.xlsx"
    df = pd.DataFrame(
        [
            ["Indikator", pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
            ["A", 1, 2],
            ["B", 3, 4],
        ]
    )
    df.to_excel(path, index=False, header=False, engine="openpyxl")
    payload = parse_excel_payload(
        str(path),
        "U",
        "v1",
        "flow",
        "monthly",
        layout_override="horizontal",
        preview_limit=2,
    )
    assert len(payload["sample"]) <= 2


def _period_to_tuple(parsed):
    return parsed["year"], parsed["month"], parsed["quarter"]


@pytest.mark.parametrize(
    ("value", "time_period", "expected"),
    [
        ("2024-01", "monthly", (2024, 1, 1)),
        ("2024-1", "monthly", (2024, 1, 1)),
        ("2024/01", "monthly", (2024, 1, 1)),
        ("2024-12-31", "monthly", (2024, 12, 4)),
        (pd.Timestamp("2024-03-01"), "monthly", (2024, 3, 1)),
        ("2024", "monthly", (None, None, None)),
        (2024, "monthly", (None, None, None)),
        ("2024-Q2", "quarterly", (2024, None, 2)),
        ("Q2-2024", "quarterly", (2024, None, 2)),
        ("2024Q3", "quarterly", (2024, None, 3)),
        (pd.Timestamp("2024-04-01"), "quarterly", (2024, None, 2)),
        ("2024", "quarterly", (None, None, None)),
        ("2024", "yearly", (2024, None, None)),
        (2024, "yearly", (2024, None, None)),
        ("43831", "yearly", (None, None, None)),
        (43831, "yearly", (None, None, None)),
    ],
)
def test_parse_period_respects_time_period(value, time_period, expected):
    assert _period_to_tuple(_parse_period(value, time_period)) == expected


def test_parse_excel_payload_yearly_accepts_numeric_year_headers(tmp_path):
    path = tmp_path / "yearly_headers.xlsx"
    df = pd.DataFrame(
        [
            ["Indikator", 2023, 2024],
            ["Contoh_Bunga", 125000, 126000],
        ]
    )
    df.to_excel(path, index=False, header=False, engine="openpyxl")

    payload = parse_excel_payload(
        str(path),
        "U",
        "v1",
        "flow",
        "yearly",
        layout_override="horizontal",
        preview_limit=10,
    )

    assert payload["layout"] == "horizontal"
    assert len(payload["entries"]) == 2
    entries = payload["entries"]
    assert entries[0]["year"] == 2023
    assert entries[0]["month"] is None
    assert entries[0]["quarter"] is None
    assert entries[1]["year"] == 2024
    assert entries[1]["month"] is None
