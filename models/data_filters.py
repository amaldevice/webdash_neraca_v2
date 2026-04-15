# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_

from infrastructure.orm_models import DataEntry
from services.period_filters import apply_period_range_filter, parse_period_filter_value, period_index


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


def build_data_entry_filter_sqlalchemy(
    data_type: Optional[str],
    time_period: Optional[str],
    uploader: Optional[str],
    indicator: Optional[str],
    period_start: Optional[str],
    period_end: Optional[str],
    value_min: Optional[float],
    value_max: Optional[float],
):
    """Combined ``WHERE`` fragment for ``DataEntry`` (mirrors ``_build_data_entry_filter_clauses``)."""
    t = DataEntry
    parts: List = []
    if data_type:
        parts.append(func.lower(t.data_type) == func.lower(data_type))
    if time_period:
        parts.append(func.lower(t.time_period) == func.lower(time_period))
    if uploader:
        pat = f"%{uploader}%"
        parts.append(func.lower(t.uploader_name).like(func.lower(pat)))
    if indicator:
        pat_i = f"%{indicator}%"
        parts.append(func.lower(t.indicator_name).like(func.lower(pat_i)))

    start_year, start_month, start_quarter = parse_period_filter_value(period_start)
    end_year, end_month, end_quarter = parse_period_filter_value(period_end)

    if time_period == "monthly":
        sm = (start_month or 1) if start_year else None
        em = (end_month or 12) if end_year else None
        if start_year is not None and sm is not None:
            parts.append(
                or_(
                    t.year > start_year,
                    and_(t.year == start_year, func.coalesce(t.month, 1) >= sm),
                )
            )
        if end_year is not None and em is not None:
            parts.append(
                or_(
                    t.year < end_year,
                    and_(t.year == end_year, func.coalesce(t.month, 12) <= em),
                )
            )
    elif time_period == "quarterly":
        sq = (start_quarter or 1) if start_year else None
        eq = (end_quarter or 4) if end_year else None
        if start_year is not None and sq is not None:
            parts.append(
                or_(
                    t.year > start_year,
                    and_(t.year == start_year, func.coalesce(t.quarter, 1) >= sq),
                )
            )
        if end_year is not None and eq is not None:
            parts.append(
                or_(
                    t.year < end_year,
                    and_(t.year == end_year, func.coalesce(t.quarter, 4) <= eq),
                )
            )
    elif time_period == "yearly":
        if start_year is not None:
            parts.append(t.year >= start_year)
        if end_year is not None:
            parts.append(t.year <= end_year)
    else:
        start_index = period_index(start_year, start_month, start_quarter, is_start=True)
        end_index = period_index(end_year, end_month, end_quarter, is_start=False)
        period_expr = t.year * 100 + func.coalesce(t.month, func.coalesce(t.quarter * 3, 1))
        if start_index is not None:
            parts.append(period_expr >= start_index)
        if end_index is not None:
            parts.append(period_expr <= end_index)

    if value_min is not None:
        parts.append(t.value >= value_min)
    if value_max is not None:
        parts.append(t.value <= value_max)

    if not parts:
        return None
    return and_(*parts)
