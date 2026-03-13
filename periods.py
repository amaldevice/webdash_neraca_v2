from __future__ import annotations

from typing import Tuple, Optional


def parse_period_date(time_period: str, period_date: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Parse period_date string into (year, month, quarter) based on time_period.

    Supported formats (case-insensitive time_period):
    - monthly:   "YYYY-MM"
    - quarterly: "YYYY-Q1" .. "YYYY-Q4"
    - yearly:    "YYYY"
    """
    try:
        period = (period_date or "").strip()
        if not period:
            return None, None, None

        tp = (time_period or "").lower()

        if tp == "monthly":
            # Format: YYYY-MM
            if "-" in period:
                parts = period.split("-")
                if len(parts) == 2:
                    year_str, month_str = parts
                    year = int(year_str)
                    month = int(month_str)
                    if 1 <= month <= 12:
                        quarter = (month - 1) // 3 + 1
                        return year, month, quarter

        elif tp == "quarterly":
            # Format: YYYY-Q1/Q2/Q3/Q4
            if "-Q" in period:
                year_str, quarter_str = period.split("-Q")
                year = int(year_str)
                quarter = int(quarter_str)
                if 1 <= quarter <= 4:
                    return year, None, quarter

        elif tp == "yearly":
            # Format: YYYY
            year = int(period)
            return year, None, None

    except (ValueError, IndexError):
        # Fall through to the default None, None, None
        pass

    return None, None, None

