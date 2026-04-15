# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

from sqlalchemy import desc, distinct, func, select
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.db import get_session, is_engine_initialized
from infrastructure.orm_models import DataEntry


def get_latest_metadata() -> Dict[str, str]:
    if not is_engine_initialized():
        return {"uploader": "Belum ada", "version": "N/A", "timestamp": "N/A"}
    try:
        session = get_session()
        stmt = (
            select(DataEntry.uploader_name, DataEntry.version, DataEntry.created_at)
            .order_by(desc(DataEntry.created_at))
            .limit(1)
        )
        row = session.execute(stmt).one_or_none()
        if not row:
            return {"uploader": "Belum ada", "version": "N/A", "timestamp": "N/A"}
        return {
            "uploader": row.uploader_name,
            "version": row.version,
            "timestamp": row.created_at,
        }
    except SQLAlchemyError:
        return {"uploader": "Belum ada", "version": "N/A", "timestamp": "N/A"}


def get_distinct_years() -> List[int]:
    """Distinct years in data_entries, descending; uses DB bound to SQLAlchemy engine."""
    if not is_engine_initialized():
        return []
    try:
        session = get_session()
        stmt = (
            select(DataEntry.year)
            .where(DataEntry.year.is_not(None))
            .distinct()
            .order_by(desc(DataEntry.year))
        )
        rows = session.execute(stmt).scalars().all()
    except SQLAlchemyError:
        return []
    years: List[int] = []
    for raw_year in rows:
        if raw_year is None:
            continue
        try:
            years.append(int(raw_year))
        except (TypeError, ValueError):
            continue
    return years


def get_aggregated_cards(limit: int = 5) -> List[Dict]:
    if not is_engine_initialized():
        return [{"title": "Belum ada data", "value": 0, "label": "—"}]
    try:
        session = get_session()
        total_indicators = session.scalar(
            select(func.count(distinct(DataEntry.indicator_name)))
        ) or 0
        total_rows = session.scalar(select(func.count()).select_from(DataEntry)) or 0
        period_rows = session.execute(
            select(DataEntry.time_period, func.count(DataEntry.id).label("count"))
            .group_by(DataEntry.time_period)
            .order_by(DataEntry.time_period)
        ).all()
    except SQLAlchemyError:
        return [{"title": "Belum ada data", "value": 0, "label": "—"}]

    period_counts = [(r.time_period, r.count) for r in period_rows]

    cards: List[Dict] = [
        {
            "title": "Total Indicators",
            "value": total_indicators,
            "label": "Unique indicators in database",
        },
        {
            "title": "Total Data Rows",
            "value": total_rows,
            "label": "Total entries in database",
        },
    ]

    period_labels = {
        "monthly": "Monthly Data",
        "quarterly": "Quarterly Data",
        "yearly": "Yearly Data",
    }

    for period in ["monthly", "quarterly", "yearly"]:
        count = 0
        for tp, c in period_counts:
            if tp == period:
                count = c
                break
        cards.append(
            {
                "title": period_labels[period],
                "value": count,
                "label": f"Data points for {period} period",
            }
        )

    if total_rows == 0:
        return [{"title": "Belum ada data", "value": 0, "label": "—"}]

    return cards[:limit]


def get_filter_options() -> Dict[str, List[str]]:
    """Get available options for filters (uploaders and indicators)"""
    if not is_engine_initialized():
        return {"uploaders": [], "indicators": []}
    try:
        session = get_session()
        uploaders = session.scalars(
            select(DataEntry.uploader_name).distinct().order_by(DataEntry.uploader_name)
        ).all()
        indicators = session.scalars(
            select(DataEntry.indicator_name).distinct().order_by(DataEntry.indicator_name)
        ).all()
        return {"uploaders": list(uploaders), "indicators": list(indicators)}
    except SQLAlchemyError:
        return {"uploaders": [], "indicators": []}


def get_unique_indicators() -> List[str]:
    """Get list of unique indicators for plot filtering"""
    if not is_engine_initialized():
        return []
    try:
        session = get_session()
        return list(
            session.scalars(
                select(DataEntry.indicator_name).distinct().order_by(DataEntry.indicator_name)
            ).all()
        )
    except SQLAlchemyError:
        return []
