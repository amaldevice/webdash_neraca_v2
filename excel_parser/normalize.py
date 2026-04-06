# -*- coding: utf-8 -*-
"""Numeric and period cell helpers for Excel parsing."""
from __future__ import annotations

import re
from typing import Dict, Optional

import pandas as pd


def _to_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip().replace("\u00a0", "").replace(" ", "")
            normalized = re.sub(r"[^0-9+\-.,]", "", normalized)
            if not normalized:
                return None

            if "," in normalized and "." in normalized:
                last_dot = normalized.rfind(".")
                last_comma = normalized.rfind(",")
                if last_comma > last_dot:
                    normalized = normalized.replace(".", "").replace(",", ".")
                else:
                    normalized = normalized.replace(",", "")
            elif "," in normalized:
                normalized = normalized.replace(".", "").replace(",", ".")

            return float(normalized)
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _is_blank(value) -> bool:
    text = _normalize_value(value)
    return text == ""


def _parse_period(period_value) -> Dict[str, Optional[int]]:
    """Parse a period value into year/month/quarter tuple."""
    try:
        parsed = pd.to_datetime(period_value, errors="coerce")
        if pd.isna(parsed):
            return {"year": None, "month": None, "quarter": None}
        return {"year": parsed.year, "month": parsed.month, "quarter": parsed.quarter}
    except Exception:
        return {"year": None, "month": None, "quarter": None}


def _looks_like_period(value) -> bool:
    return _parse_period(value)["year"] is not None


def _trim_sparse_data(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully empty rows/columns to reduce noise from metadata-only cells."""
    if df.empty:
        return df
    trimmed = df.dropna(how="all")
    if trimmed.empty:
        return trimmed
    trimmed = trimmed.loc[:, trimmed.notna().any(axis=0)]
    return trimmed


def _count_period_cells(values) -> int:
    return sum(1 for value in values if _looks_like_period(value))


def _row_non_empty_count(row) -> int:
    return sum(1 for value in row if not _is_blank(value))
