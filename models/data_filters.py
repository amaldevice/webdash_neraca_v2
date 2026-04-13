# -*- coding: utf-8 -*-
from typing import List, Optional, Tuple

from services.period_filters import apply_period_range_filter


def _build_data_entry_filter_clauses(
    data_type: Optional[str],
    time_period: Optional[str],
    uploader: Optional[str],
    indicator: Optional[str],
    period_start: Optional[str],
    period_end: Optional[str],
    value_min: Optional[float],
    value_max: Optional[float],
) -> Tuple[List[str], List]:
    clauses: List[str] = []
    params: List = []
    if data_type:
        clauses.append("LOWER(data_type) = LOWER(?)")
        params.append(data_type)
    if time_period:
        clauses.append("LOWER(time_period) = LOWER(?)")
        params.append(time_period)
    if uploader:
        clauses.append("LOWER(uploader_name) LIKE LOWER(?)")
        params.append(f"%{uploader}%")
    if indicator:
        clauses.append("LOWER(indicator_name) LIKE LOWER(?)")
        params.append(f"%{indicator}%")

    apply_period_range_filter(
        clauses=clauses,
        params=params,
        time_period_filter=time_period,
        period_start=period_start,
        period_end=period_end,
    )

    if value_min is not None:
        clauses.append("value >= ?")
        params.append(value_min)
    if value_max is not None:
        clauses.append("value <= ?")
        params.append(value_max)
    return clauses, params
