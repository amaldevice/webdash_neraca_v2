# -*- coding: utf-8 -*-
"""Build normalized DB-shaped records from Excel cells."""
from __future__ import annotations

from typing import Dict, Optional

from services.timeutil import utc_now_iso

from excel_parser.normalize import _parse_period, _to_float


def _period_text(entry: dict) -> str:
    year = entry.get("year")
    month = entry.get("month")
    quarter = entry.get("quarter")
    if year is None:
        return "-"
    if month:
        return f"{int(year)}-{int(month):02d}"
    if quarter:
        return f"{int(year)}-Q{int(quarter)}"
    return str(year)


def _normalize_record(
    *,
    uploader: str,
    version: str,
    layout: str,
    data_type: str,
    time_period: str,
    indicator: str,
    value,
    period_value,
) -> Optional[Dict]:
    parsed_value = _to_float(value)
    if parsed_value is None or not indicator:
        return None
    parsed_period = _parse_period(period_value)
    return {
        "uploader_name": uploader,
        "version": version,
        "template_type": layout,
        "data_type": data_type.lower().strip(),
        "time_period": time_period.lower().strip(),
        "indicator_name": str(indicator).strip(),
        "value": parsed_value,
        "unit": None,
        "region_code": None,
        "year": parsed_period["year"],
        "month": parsed_period["month"],
        "quarter": parsed_period["quarter"],
        "created_at": utc_now_iso(),
    }
