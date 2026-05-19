# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
from excel_parser.timeutil import utc_now_iso


def test_utc_now_iso_returns_iso_string():
    s = utc_now_iso()
    assert isinstance(s, str)
    assert "T" in s and "+" not in s
    parsed = datetime.fromisoformat(s)
    assert parsed.tzinfo is None


import pandas as pd
from services.dataset_catalog import get_dataset
from excel_parser.dataset_long import try_parse_universal_long_dataframe


def test_universal_long_created_at_is_string():
    definition = get_dataset("universal")
    df = pd.DataFrame(
        {
            "nama_dataset": ["PLN"],
            "indikator": ["Pelanggan"],
            "periode": ["2024-01"],
            "nilai": [100.0],
        }
    )
    entries = try_parse_universal_long_dataframe(
        df, definition, uploader="test", version="v1", data_type="flow", form_time_period="monthly",
    )
    assert entries is not None and len(entries) == 1
    assert isinstance(entries[0]["created_at"], str)
