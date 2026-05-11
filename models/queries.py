# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.db import get_session, is_engine_initialized

from .data_filters import build_data_entry_filter_sqlalchemy


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
        "dataset_code": row.get("dataset_code", ""),
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
    dataset_code: Optional[str] = None,
    *,
    session: Session,
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
        dataset_code,
    )
    stmt = select(func.count(DataEntry.id)).select_from(DataEntry)
    if where is not None:
        stmt = stmt.where(where)
    try:
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
    dataset_code: Optional[str] = None,
    *,
    session: Session | None = None,
) -> int:
    if session is None and not is_engine_initialized():
        return 0
    try:
        sess = session if session is not None else get_session()
    except SQLAlchemyError:
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
        dataset_code,
        session=sess,
    )


def _sa_get_landing_summary(*, session: Session) -> Dict[str, Any]:
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


def get_landing_summary(*, session: Session | None = None) -> Dict[str, Any]:
    if session is None and not is_engine_initialized():
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
    try:
        sess = session if session is not None else get_session()
    except SQLAlchemyError:
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
    return _sa_get_landing_summary(session=sess)


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
    dataset_code: Optional[str] = None,
    *,
    session: Session,
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
        dataset_code,
    )
    safe_offset = offset if offset is not None and offset >= 0 else 0
    stmt = select(DataEntry)
    if where is not None:
        stmt = stmt.where(where)
    stmt = stmt.order_by(desc(DataEntry.created_at)).limit(limit).offset(safe_offset)
    try:
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
            "dataset_code": getattr(row, "dataset_code", "") or "",
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
    dataset_code: Optional[str] = None,
    *,
    session: Session | None = None,
) -> List[Dict]:
    if session is None and not is_engine_initialized():
        return []
    try:
        sess = session if session is not None else get_session()
    except SQLAlchemyError:
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
        dataset_code,
        session=sess,
    )



def preview_duplicates_batches(
    unique_keys: Sequence[Tuple[Any, ...]],
    *,
    session: Session | None = None,
) -> List[Dict[str, Any]]:
    """Load existing rows matching (indicator_name, year, month, quarter, dataset_code) keys in batches."""
    if not unique_keys:
        return []
    if session is None and not is_engine_initialized():
        return []

    from infrastructure.orm_models import DataEntry

    def one_key(indicator: Any, year: Any, month: Any, quarter: Any, ds_code: Any):
        parts = [DataEntry.indicator_name == indicator, DataEntry.year == year]
        if month is None:
            parts.append(DataEntry.month.is_(None))
        else:
            parts.append(DataEntry.month == month)
        if quarter is None:
            parts.append(DataEntry.quarter.is_(None))
        else:
            parts.append(DataEntry.quarter == quarter)
        dc = (ds_code or "").strip()
        parts.append(DataEntry.dataset_code == dc)
        return and_(*parts)

    max_batch_size = max(1, 999 // 5)
    out: List[Dict[str, Any]] = []
    try:
        sess = session if session is not None else get_session()
    except SQLAlchemyError:
        return []
    try:
        for offset in range(0, len(unique_keys), max_batch_size):
            batch = unique_keys[offset : offset + max_batch_size]
            ors = []
            for tup in batch:
                if len(tup) == 4:
                    i, y, m, q = tup
                    dc = ""
                else:
                    i, y, m, q, dc = tup[0], tup[1], tup[2], tup[3], tup[4]
                ors.append(one_key(i, y, m, q, dc))
            stmt = select(DataEntry).where(or_(*ors))
            for row in sess.scalars(stmt).all():
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
                        "dataset_code": getattr(row, "dataset_code", "") or "",
                    }
                )
    except SQLAlchemyError:
        return []
    return out
