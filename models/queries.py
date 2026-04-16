# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.db import get_session, is_engine_initialized

from .data_filters import build_data_entry_filter_sqlalchemy, period_analysis_range_sqlalchemy


def _format_period_text_from_parts(year: Any, month: Any, quarter: Any) -> str:
    if year is None:
        return "N/A"

    year_int = int(year)
    if month is not None:
        month_int = int(month)
        return f"{year_int}-{month_int:02d}"

    if quarter is not None:
        quarter_int = int(quarter)
        return f"{year_int}-Q{quarter_int}"

    return str(year_int)


def _row_to_public_dict(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Public row shape for list/preview routes (includes ``tanggal_data``)."""
    year = row["year"]
    month = row["month"]
    quarter = row["quarter"]
    return {
        "id": row["id"],
        "uploader_name": row["uploader_name"],
        "version": row["version"],
        "indicator_name": row["indicator_name"],
        "value": row["value"],
        "data_type": row["data_type"],
        "time_period": row["time_period"],
        "created_at": row["created_at"],
        "year": year,
        "month": month,
        "quarter": quarter,
        "tanggal_data": _format_period_text_from_parts(year, month, quarter),
    }


def _sa_get_total_entries_count(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    value_min: Optional[float] = None,
    value_max: Optional[float] = None,
) -> int:
    from infrastructure.orm_models import DataEntry

    where = build_data_entry_filter_sqlalchemy(
        data_type,
        time_period,
        uploader,
        indicator,
        period_start,
        period_end,
        value_min,
        value_max,
    )
    stmt = select(func.count(DataEntry.id)).select_from(DataEntry)
    if where is not None:
        stmt = stmt.where(where)
    try:
        session = get_session()
        n = session.execute(stmt).scalar_one()
        return int(n) if n is not None else 0
    except SQLAlchemyError:
        return 0


def get_total_entries_count(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    value_min: Optional[float] = None,
    value_max: Optional[float] = None,
) -> int:
    if not is_engine_initialized():
        return 0
    return _sa_get_total_entries_count(
        data_type,
        time_period,
        uploader,
        indicator,
        period_start,
        period_end,
        value_min,
        value_max,
    )


def _sa_get_landing_summary() -> Dict[str, Any]:
    from infrastructure.orm_models import DataEntry

    summary = {
        "total_data_rows": 0,
        "total_indicators": 0,
        "monthly_rows": 0,
        "quarterly_rows": 0,
        "yearly_rows": 0,
        "latest_uploader": None,
        "latest_version": None,
        "latest_created_at": None,
    }

    metrics_stmt = select(
        func.count(DataEntry.id).label("total_data_rows"),
        func.count(func.distinct(DataEntry.indicator_name)).label("total_indicators"),
        func.sum(case((DataEntry.time_period == "monthly", 1), else_=0)).label("monthly_rows"),
        func.sum(case((DataEntry.time_period == "quarterly", 1), else_=0)).label("quarterly_rows"),
        func.sum(case((DataEntry.time_period == "yearly", 1), else_=0)).label("yearly_rows"),
    )
    latest_stmt = (
        select(DataEntry.uploader_name, DataEntry.version, DataEntry.created_at)
        .order_by(desc(DataEntry.created_at), desc(DataEntry.id))
        .limit(1)
    )

    try:
        session = get_session()
        metrics_row = session.execute(metrics_stmt).one()
        latest_row = session.execute(latest_stmt).one_or_none()

        summary["total_data_rows"] = int(metrics_row.total_data_rows or 0)
        summary["total_indicators"] = int(metrics_row.total_indicators or 0)
        summary["monthly_rows"] = int(metrics_row.monthly_rows or 0)
        summary["quarterly_rows"] = int(metrics_row.quarterly_rows or 0)
        summary["yearly_rows"] = int(metrics_row.yearly_rows or 0)
        if latest_row is not None:
            summary["latest_uploader"] = latest_row.uploader_name
            summary["latest_version"] = latest_row.version
            summary["latest_created_at"] = latest_row.created_at
    except SQLAlchemyError:
        pass

    return summary


def get_landing_summary() -> Dict[str, Any]:
    if not is_engine_initialized():
        return {
            "total_data_rows": 0,
            "total_indicators": 0,
            "monthly_rows": 0,
            "quarterly_rows": 0,
            "yearly_rows": 0,
            "latest_uploader": None,
            "latest_version": None,
            "latest_created_at": None,
        }
    return _sa_get_landing_summary()


def _sa_query_data_entries(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    limit: int = 100,
    offset: Optional[int] = 0,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    value_min: Optional[float] = None,
    value_max: Optional[float] = None,
) -> List[Dict[str, Any]]:
    from infrastructure.orm_models import DataEntry

    where = build_data_entry_filter_sqlalchemy(
        data_type,
        time_period,
        uploader,
        indicator,
        period_start,
        period_end,
        value_min,
        value_max,
    )
    safe_offset = offset if offset is not None and offset >= 0 else 0
    stmt = select(DataEntry)
    if where is not None:
        stmt = stmt.where(where)
    stmt = stmt.order_by(desc(DataEntry.created_at)).limit(limit).offset(safe_offset)
    try:
        session = get_session()
        rows = session.scalars(stmt).all()
    except SQLAlchemyError:
        return []

    out: List[Dict[str, Any]] = []
    for row in rows:
        mapping = {
            "id": row.id,
            "uploader_name": row.uploader_name,
            "version": row.version,
            "indicator_name": row.indicator_name,
            "value": row.value,
            "data_type": row.data_type,
            "time_period": row.time_period,
            "created_at": row.created_at,
            "year": row.year,
            "month": row.month,
            "quarter": row.quarter,
        }
        out.append(_row_to_public_dict(mapping))
    return out


def query_data_entries(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    limit: int = 100,
    offset: Optional[int] = 0,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    value_min: Optional[float] = None,
    value_max: Optional[float] = None,
) -> List[Dict]:
    if not is_engine_initialized():
        return []
    return _sa_query_data_entries(
        data_type,
        time_period,
        uploader,
        indicator,
        limit,
        offset,
        period_start,
        period_end,
        value_min,
        value_max,
    )


def fetch_series_for_comparison(
    indicator: str,
    analysis_year: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Rows for period-analysis calculators (indicator + optional year + period range)."""
    if not is_engine_initialized():
        return []
    from infrastructure.orm_models import DataEntry

    t = DataEntry
    w: List[Any] = [t.indicator_name == indicator, t.year.isnot(None)]
    if analysis_year:
        w.append(t.year == int(analysis_year))
    pr = period_analysis_range_sqlalchemy(period_start, period_end)
    if pr is not None:
        w.append(pr)
    stmt = (
        select(t.year, t.month, t.quarter, t.value, t.time_period, t.data_type)
        .where(and_(*w))
        .order_by(t.year, t.month, t.quarter)
    )
    out: List[Dict[str, Any]] = []
    try:
        session = get_session()
        for y, m, q, val, tp, dt in session.execute(stmt):
            out.append(
                {
                    "year": y,
                    "month": m,
                    "quarter": q,
                    "value": val,
                    "time_period": tp,
                    "data_type": dt,
                }
            )
    except SQLAlchemyError:
        return []
    return out


def preview_duplicates_batches(
    unique_keys: Sequence[Tuple[Any, Any, Any, Any]],
) -> List[Dict[str, Any]]:
    """Load existing rows matching (indicator_name, year, month, quarter) keys in batches."""
    if not unique_keys or not is_engine_initialized():
        return []

    from infrastructure.orm_models import DataEntry

    def one_key(indicator: Any, year: Any, month: Any, quarter: Any):
        parts = [DataEntry.indicator_name == indicator, DataEntry.year == year]
        if month is None:
            parts.append(DataEntry.month.is_(None))
        else:
            parts.append(DataEntry.month == month)
        if quarter is None:
            parts.append(DataEntry.quarter.is_(None))
        else:
            parts.append(DataEntry.quarter == quarter)
        return and_(*parts)

    max_batch_size = max(1, 999 // 4)
    out: List[Dict[str, Any]] = []
    try:
        session = get_session()
        for offset in range(0, len(unique_keys), max_batch_size):
            batch = unique_keys[offset : offset + max_batch_size]
            ors = [one_key(i, y, m, q) for i, y, m, q in batch]
            stmt = select(DataEntry).where(or_(*ors))
            for row in session.scalars(stmt).all():
                out.append(
                    {
                        "id": row.id,
                        "uploader_name": row.uploader_name,
                        "version": row.version,
                        "indicator_name": row.indicator_name,
                        "year": row.year,
                        "month": row.month,
                        "quarter": row.quarter,
                        "value": row.value,
                    }
                )
    except SQLAlchemyError:
        return []
    return out
