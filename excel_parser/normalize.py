# -*- coding: utf-8 -*-
"""Numeric and period cell helpers for Excel parsing."""
from __future__ import annotations

import re
from typing import Dict, Optional

import pandas as pd


_MONTHLY_PERIOD_RE = re.compile(r"^\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?$")
_YEARLY_PERIOD_RE = re.compile(r"^\d{4}$")
_QUARTERLY_PERIOD_RE_1 = re.compile(r"^(?P<year>\d{4})\s*[-/]?\s*Q(?P<quarter>[1-4])$", re.I)
_QUARTERLY_PERIOD_RE_2 = re.compile(r"^Q(?P<quarter>[1-4])\s*[-/]?\s*(?P<year>\d{4})$", re.I)


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


def _to_datetime(period_value) -> Optional[pd.Timestamp]:
    try:
        parsed = pd.to_datetime(period_value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed
    except Exception:
        return None


def _parse_yearly_period(period_value, normalized: str) -> Dict[str, Optional[int]]:
    if pd.api.types.is_bool(period_value):
        return {"year": None, "month": None, "quarter": None}

    if _YEARLY_PERIOD_RE.fullmatch(normalized):
        year = int(normalized)
        return {"year": year, "month": None, "quarter": None}
    if normalized.isdigit():
        return {"year": None, "month": None, "quarter": None}

    if isinstance(period_value, (int, float)):
        if isinstance(period_value, bool):
            return {"year": None, "month": None, "quarter": None}
        if float(period_value).is_integer():
            year = int(period_value)
            if 1 <= year <= 9999:
                return {"year": year, "month": None, "quarter": None}
        return {"year": None, "month": None, "quarter": None}

    parsed = _to_datetime(period_value)
    if parsed is None:
        return {"year": None, "month": None, "quarter": None}
    return {"year": parsed.year, "month": parsed.month, "quarter": None}


def _parse_quarterly_period(period_value, normalized: str) -> Dict[str, Optional[int]]:
    if pd.api.types.is_bool(period_value):
        return {"year": None, "month": None, "quarter": None}

    m1 = _QUARTERLY_PERIOD_RE_1.fullmatch(normalized)
    if m1:
        return {
            "year": int(m1.group("year")),
            "month": None,
            "quarter": int(m1.group("quarter")),
        }

    m2 = _QUARTERLY_PERIOD_RE_2.fullmatch(normalized)
    if m2:
        return {
            "year": int(m2.group("year")),
            "month": None,
            "quarter": int(m2.group("quarter")),
        }

    parsed = _to_datetime(period_value)
    if parsed is None:
        return {"year": None, "month": None, "quarter": None}
    return {"year": parsed.year, "month": parsed.month, "quarter": parsed.quarter}


def _parse_monthly_period(period_value, normalized: str) -> Dict[str, Optional[int]]:
    if pd.api.types.is_bool(period_value):
        return {"year": None, "month": None, "quarter": None}

    if isinstance(period_value, (int, float)) and not pd.api.types.is_bool(period_value):
        return {"year": None, "month": None, "quarter": None}

    if _YEARLY_PERIOD_RE.fullmatch(normalized):
        return {"year": None, "month": None, "quarter": None}
    if normalized.isdigit():
        return {"year": None, "month": None, "quarter": None}

    if _MONTHLY_PERIOD_RE.fullmatch(normalized):
        parsed = _to_datetime(normalized)
        if parsed is None:
            return {"year": None, "month": None, "quarter": None}
        return {"year": parsed.year, "month": parsed.month, "quarter": parsed.quarter}

    parsed = _to_datetime(period_value)
    if parsed is None:
        return {"year": None, "month": None, "quarter": None}
    return {"year": parsed.year, "month": parsed.month, "quarter": parsed.quarter}


def _parse_period(period_value, time_period: str | None = None) -> Dict[str, Optional[int]]:
    """Parse a period value into year/month/quarter tuple."""
    try:
        normalized = _normalize_value(period_value)
        if not normalized:
            return {"year": None, "month": None, "quarter": None}

        period_type = (time_period or "").strip().lower()
        if period_type == "yearly":
            return _parse_yearly_period(period_value, normalized)
        if period_type == "quarterly":
            return _parse_quarterly_period(period_value, normalized)
        if period_type == "monthly":
            return _parse_monthly_period(period_value, normalized)

        parsed = _to_datetime(period_value)
        if parsed is None:
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
