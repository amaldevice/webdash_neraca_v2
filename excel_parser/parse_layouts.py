# -*- coding: utf-8 -*-
"""Vertical / horizontal sheet parsing into entry dicts."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from excel_parser.normalize import _is_blank
from excel_parser.records import _normalize_record


def _parse_vertical_layout(
    df: pd.DataFrame,
    *,
    diagnostics: Optional[Dict[str, List[int]]] = None,
    **kwargs,
) -> List[Dict]:
    entries: List[Dict] = []
    invalid_rows: set[int] = set()

    for _, row in df.iterrows():
        period_value = row.iloc[0]
        period_row_display = int(row.name) + 1
        if _is_blank(period_value):
            invalid_rows.add(period_row_display)
            continue
        period_indicators = set()

        for indicator, value in row.iloc[1:].items():
            if indicator in period_indicators:
                continue
            if _is_blank(indicator):
                continue

            record = _normalize_record(
                indicator=indicator,
                value=value,
                period_value=period_value,
                **kwargs,
            )
            if record:
                entries.append(record)
                period_indicators.add(indicator)
            else:
                invalid_rows.add(period_row_display)

    if diagnostics is not None:
        diagnostics["invalid_rows"] = sorted(invalid_rows)

    return entries


def _parse_horizontal_layout(
    df: pd.DataFrame,
    *,
    diagnostics: Optional[Dict[str, List[int]]] = None,
    **kwargs,
) -> List[Dict]:
    entries: List[Dict] = []
    headers = df.columns[1:]
    invalid_rows: set[int] = set()
    for _, row in df.iterrows():
        indicator = row.iloc[0]
        indicator_row_display = int(row.name) + 1
        if _is_blank(indicator):
            invalid_rows.add(indicator_row_display)
            continue
        for period_value, value in zip(headers, row.iloc[1:]):
            record = _normalize_record(
                indicator=indicator,
                value=value,
                period_value=period_value,
                **kwargs,
            )
            if record:
                entries.append(record)
            else:
                invalid_rows.add(indicator_row_display)

    if diagnostics is not None:
        diagnostics["invalid_rows"] = sorted(invalid_rows)

    return entries
