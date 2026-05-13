# -*- coding: utf-8 -*-
"""Raw export CSV/Excel column parity (GitHub #81)."""
from __future__ import annotations

import csv
from io import BytesIO, StringIO

import pandas as pd

from services.raw_export import RAW_EXPORT_COLUMNS, build_raw_data_export_response


def test_raw_export_csv_and_excel_share_column_order():
    row = {col: col for col in RAW_EXPORT_COLUMNS}
    csv_resp = build_raw_data_export_response([row], "csv")
    csv_reader = csv.reader(StringIO(csv_resp.get_data(as_text=True)))
    assert next(csv_reader) == RAW_EXPORT_COLUMNS

    xlsx_resp = build_raw_data_export_response([row], "excel")
    df = pd.read_excel(BytesIO(xlsx_resp.data))
    assert list(df.columns) == RAW_EXPORT_COLUMNS
