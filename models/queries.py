# -*- coding: utf-8 -*-
from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from config import use_sqlalchemy
from infrastructure.db import get_session, is_engine_initialized

from .connection import get_conn
from services.period_filters import apply_period_range_filter

from .data_filters import (
    _build_data_entry_filter_clauses,
    build_data_entry_filter_sqlalchemy,
    period_analysis_range_sqlalchemy,
)


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


def _use_sqlalchemy_reads() -> bool:
    return use_sqlalchemy() and is_engine_initialized()


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


def _legacy_get_total_entries_count(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    value_min: Optional[float] = None,
    value_max: Optional[float] = None,
) -> int:
    clauses, params = _build_data_entry_filter_clauses(
        data_type, time_period, uploader, indicator, period_start, period_end, value_min, value_max
    )

    base_query = "SELECT COUNT(*) FROM data_entries"
    if clauses:
        base_query += " WHERE " + " AND ".join(clauses)

    try:
        with closing(get_conn()) as conn:
            row = conn.execute(base_query, tuple(params)).fetchone()
            return row[0] if row else 0
    except sqlite3.OperationalError:
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
    if _use_sqlalchemy_reads():
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
    return _legacy_get_total_entries_count(
        data_type,
        time_period,
        uploader,
        indicator,
        period_start,
        period_end,
        value_min,
        value_max,
    )


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


def _legacy_query_data_entries(
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
    clauses, params = _build_data_entry_filter_clauses(
        data_type, time_period, uploader, indicator, period_start, period_end, value_min, value_max
    )

    base_query = """
        SELECT id, uploader_name, version, indicator_name, value, data_type, time_period, created_at,
               year, month, quarter
        FROM data_entries
    """
    if clauses:
        base_query += " WHERE " + " AND ".join(clauses)
    base_query += " ORDER BY datetime(created_at) DESC LIMIT ? OFFSET ?"
    safe_offset = offset if offset is not None and offset >= 0 else 0
    params.extend([limit, safe_offset])

    try:
        with closing(get_conn()) as conn:
            rows = conn.execute(base_query, tuple(params)).fetchall()
    except sqlite3.OperationalError:
        return []

    return [_row_to_public_dict(row) for row in rows]


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
    if _use_sqlalchemy_reads():
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
    return _legacy_query_data_entries(
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


def _sa_fetch_series_for_comparison(
    indicator: str,
    analysis_year: Optional[str],
    period_start: Optional[str],
    period_end: Optional[str],
) -> List[Dict[str, Any]]:
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


def fetch_series_for_comparison(
    indicator: str,
    analysis_year: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Rows for period-analysis calculators (indicator + optional year + period range)."""
    if _use_sqlalchemy_reads():
        return _sa_fetch_series_for_comparison(
            indicator, analysis_year, period_start, period_end
        )

    period_clauses: List[str] = []
    period_params: List[Any] = []
    apply_period_range_filter(
        period_clauses,
        period_params,
        None,
        period_start,
        period_end,
    )

    base_query = """
        SELECT year, month, quarter, value, time_period, data_type
        FROM data_entries
        WHERE indicator_name = ? AND year IS NOT NULL
    """
    params: List[Any] = [indicator]
    if analysis_year:
        base_query += " AND year = ?"
        params.append(int(analysis_year))
    if period_clauses:
        base_query += " AND " + " AND ".join(period_clauses)
        params.extend(period_params)
    base_query += " ORDER BY year, month, quarter"

    with closing(get_conn()) as conn:
        rows = conn.execute(base_query, params).fetchall()

    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "year": row["year"],
                "month": row["month"],
                "quarter": row["quarter"],
                "value": row["value"],
                "time_period": row["time_period"],
                "data_type": row["data_type"],
            }
        )
    return out


def _sa_preview_duplicates_batches(
    unique_keys: Sequence[Tuple[Any, Any, Any, Any]],
) -> List[Dict[str, Any]]:
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


def _preview_dup_match_clause(
    params: List[Any],
    indicator: Any,
    year: Any,
    month: Any,
    quarter: Any,
) -> str:
    clauses = ["indicator_name = ?", "year = ?"]
    params.extend([indicator, year])
    if month is None:
        clauses.append("month IS NULL")
    else:
        clauses.append("month = ?")
        params.append(month)
    if quarter is None:
        clauses.append("quarter IS NULL")
    else:
        clauses.append("quarter = ?")
        params.append(quarter)
    return "(" + " AND ".join(clauses) + ")"


def preview_duplicates_batches(
    unique_keys: Sequence[Tuple[Any, Any, Any, Any]],
) -> List[Dict[str, Any]]:
    """
    Load existing rows matching (indicator_name, year, month, quarter) keys in batches (bind limit ~999).

    Uses SQLAlchemy when ``DATABASE_URL`` + engine active; otherwise legacy ``sqlite3`` connection.
    """
    if not unique_keys:
        return []

    if _use_sqlalchemy_reads():
        return _sa_preview_duplicates_batches(unique_keys)

    max_batch_size = max(1, 999 // 4)
    all_rows: List[Any] = []
    for offset in range(0, len(unique_keys), max_batch_size):
        batch = unique_keys[offset : offset + max_batch_size]
        params: List[Any] = []
        where_parts: List[str] = []
        for indicator, year, month, quarter in batch:
            where_parts.append(
                _preview_dup_match_clause(params, indicator, year, month, quarter)
            )
        sql = f"""
            SELECT id, uploader_name, version, indicator_name, year, month, quarter, value
            FROM data_entries
            WHERE {" OR ".join(where_parts)}
        """
        with closing(get_conn()) as conn:
            all_rows.extend(conn.execute(sql, params).fetchall())

    return [
        {
            "id": row["id"],
            "uploader_name": row["uploader_name"],
            "version": row["version"],
            "indicator_name": row["indicator_name"],
            "year": row["year"],
            "month": row["month"],
            "quarter": row["quarter"],
            "value": row["value"],
        }
        for row in all_rows
    ]
