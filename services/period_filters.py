# -*- coding: utf-8 -*-
"""SQL period-range helpers for listing/count queries (no DB I/O)."""
from __future__ import annotations

import re
from typing import Optional


def parse_period_filter_value(
    period_value: Optional[str],
) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """Parse an input period value into (year, month, quarter)."""
    if not period_value:
        return None, None, None

    normalized = str(period_value).strip().upper()
    if not normalized:
        return None, None, None

    quarterly_match = re.fullmatch(r"^(\d{4})-Q([1-4])$", normalized)
    if quarterly_match:
        year = int(quarterly_match.group(1))
        quarter = int(quarterly_match.group(2))
        return year, None, quarter

    monthly_match = re.fullmatch(r"^(\d{4})-(\d{1,2})$", normalized)
    if monthly_match:
        year = int(monthly_match.group(1))
        month = int(monthly_match.group(2))
        if 1 <= month <= 12:
            return year, month, None
        return None, None, None

    year_match = re.fullmatch(r"^(\d{4})$", normalized)
    if year_match:
        return int(year_match.group(1)), None, None

    return None, None, None


def period_index(
    year: Optional[int],
    month: Optional[int],
    quarter: Optional[int],
    is_start: bool,
) -> Optional[int]:
    """Convert a parsed period to a comparable month index (YYYYMM-style)."""
    if year is None:
        return None

    if month:
        return year * 100 + month

    if quarter:
        normalized_quarter = max(1, min(4, quarter))
        return year * 100 + ((normalized_quarter - 1) * 3 + (1 if is_start else 3))

    return year * 100 + (1 if is_start else 12)
