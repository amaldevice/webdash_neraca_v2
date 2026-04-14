# -*- coding: utf-8 -*-
import sqlite3
from contextlib import closing
from typing import Dict, List, Optional

from .connection import get_conn
from .data_filters import _build_data_entry_filter_clauses


def _format_period_text(row: sqlite3.Row) -> str:
    year = row["year"]
    month = row["month"]
    quarter = row["quarter"]

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

    return [
        {
            "id": row["id"],
            "uploader_name": row["uploader_name"],
            "version": row["version"],
            "indicator_name": row["indicator_name"],
            "value": row["value"],
            "data_type": row["data_type"],
            "time_period": row["time_period"],
            "created_at": row["created_at"],
            "year": row["year"],
            "month": row["month"],
            "quarter": row["quarter"],
            "tanggal_data": _format_period_text(row),
        }
        for row in rows
    ]
