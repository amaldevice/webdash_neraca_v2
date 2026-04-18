from __future__ import annotations

from typing import Tuple, Optional


def parse_period_date(time_period: str, period_date: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Parse period_date string into (year, month, quarter) based on time_period.

    Supported formats (case-insensitive time_period):
    - monthly:   "YYYY-MM"
    - quarterly: "YYYY-Q1" .. "YYYY-Q4" (fallback to "YYYY-MM" for compatibility)
    - yearly:    "YYYY" (fallback to "YYYY-MM" as period marker)
    """
    period = (period_date or "").strip()
    if not period:
        return None, None, None

    tp = (time_period or "").lower()

    def _parse_year_month(value: str) -> Tuple[Optional[int], Optional[int]]:
        parts = value.split("-")
        if len(parts) != 2:
            return None, None
        year_str, month_str = parts
        if not year_str.isdigit() or not month_str.isdigit():
            return None, None
        year = int(year_str)
        month = int(month_str)
        if not (1 <= month <= 12):
            return None, None
        return year, month

    if tp == "monthly":
        # Format: YYYY-MM
        year, month = _parse_year_month(period)
        if year is None or month is None:
            return None, None, None
        quarter = (month - 1) // 3 + 1
        return year, month, quarter

    if tp == "quarterly":
        # Prefer YYYY-Q1/Q2/Q3/Q4 (case-insensitive), fallback YYYY-MM.
        upper_period = period.upper()
        if "-Q" in upper_period:
            year_str, quarter_str = upper_period.split("-Q")
            try:
                year = int(year_str)
                quarter = int(quarter_str)
            except (ValueError, IndexError):
                return None, None, None
            if 1 <= quarter <= 4:
                return year, None, quarter
        year, month = _parse_year_month(period)
        if year is None or month is None:
            return None, None, None
        quarter = (month - 1) // 3 + 1
        return year, month, quarter

    if tp == "yearly":
        # Format: YYYY
        if period.isdigit():
            return int(period), None, None
        # Fallback marker format YYYY-MM for user-defined yearly labels.
        year, month = _parse_year_month(period)
        if year is None:
            return None, None, None
        return year, month, None

    return None, None, None

