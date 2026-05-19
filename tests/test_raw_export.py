# -*- coding: utf-8 -*-
"""Raw export CSV/Excel column parity (GitHub #81)."""
from __future__ import annotations

import csv
from io import BytesIO, StringIO

import pandas as pd

from services.entry_list_page import EXPORT_ENTRY_HARD_CAP
from services.raw_export import RAW_EXPORT_COLUMNS, build_raw_data_export_response


def test_raw_export_csv_and_excel_share_column_order():
    row = {col: col for col in RAW_EXPORT_COLUMNS}
    csv_resp = build_raw_data_export_response([row], "csv")
    csv_reader = csv.reader(StringIO(csv_resp.get_data(as_text=True)))
    assert next(csv_reader) == RAW_EXPORT_COLUMNS

    xlsx_resp = build_raw_data_export_response([row], "excel")
    df = pd.read_excel(BytesIO(xlsx_resp.data))
    assert list(df.columns) == RAW_EXPORT_COLUMNS


def test_export_hard_cap_truncates_excess_rows_csv():
    """Rows > EXPORT_ENTRY_HARD_CAP must be silently truncated (regression guard for #80)."""
    over = EXPORT_ENTRY_HARD_CAP + 5
    rows = [{col: i for col in RAW_EXPORT_COLUMNS} for i in range(over)]
    resp = build_raw_data_export_response(rows, "csv")
    reader = csv.reader(StringIO(resp.get_data(as_text=True)))
    next(reader)  # skip header
    data_rows = list(reader)
    assert len(data_rows) == EXPORT_ENTRY_HARD_CAP


def test_export_hard_cap_truncates_excess_rows_excel():
    """Excel path must also respect EXPORT_ENTRY_HARD_CAP (regression guard for #80)."""
    over = EXPORT_ENTRY_HARD_CAP + 5
    rows = [{col: i for col in RAW_EXPORT_COLUMNS} for i in range(over)]
    resp = build_raw_data_export_response(rows, "excel")
    df = pd.read_excel(BytesIO(resp.data))
    assert len(df) == EXPORT_ENTRY_HARD_CAP
