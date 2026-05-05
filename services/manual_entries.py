# -*- coding: utf-8 -*-
from __future__ import annotations

from periods import parse_period_date
from services.timeutil import utc_now_iso


def build_manual_entry(
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    period_date: str,
    indicator: str,
    value: str,
    *,
    dataset_slug: str = "",
) -> dict | None:
    try:
        parsed_value = float(value)
    except ValueError:
        return None

    year, month, quarter = parse_period_date(time_period, period_date)
    ds = (dataset_slug or "").strip()

    return {
        "uploader_name": uploader,
        "version": version,
        "template_type": "manual",
        "data_type": data_type.lower() or "flow",
        "time_period": time_period.lower() or "monthly",
        "indicator_name": indicator,
        "value": parsed_value,
        "unit": None,
        "region_code": None,
        "year": year,
        "month": month,
        "quarter": quarter,
        "created_at": utc_now_iso(),
        "dataset_code": ds,
    }
