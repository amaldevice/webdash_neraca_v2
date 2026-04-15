# -*- coding: utf-8 -*-
from __future__ import annotations

from contextlib import closing
from typing import Dict, List

from sqlalchemy import desc, distinct, func, select
from sqlalchemy.exc import SQLAlchemyError

from config import use_sqlalchemy
from infrastructure.db import get_session, is_engine_initialized
from infrastructure.orm_models import DataEntry

from .connection import get_conn


def _use_sqlalchemy_reads() -> bool:
    return use_sqlalchemy() and is_engine_initialized()


def get_latest_metadata() -> Dict[str, str]:
    if _use_sqlalchemy_reads():
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

    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT uploader_name, version, created_at
            FROM data_entries
            ORDER BY datetime(created_at) DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return {"uploader": "Belum ada", "version": "N/A", "timestamp": "N/A"}
        return {
            "uploader": row["uploader_name"],
            "version": row["version"],
            "timestamp": row["created_at"],
        }


def get_distinct_years() -> List[int]:
    """Distinct years in data_entries, descending; uses DB_PATH (test-patched via models)."""
    if _use_sqlalchemy_reads():
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

    years: List[int] = []
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT year
            FROM data_entries
            WHERE year IS NOT NULL
            ORDER BY year DESC
            """
        ).fetchall()
    for row in rows:
        raw_year = row[0]
        if raw_year is None:
            continue
        try:
            years.append(int(raw_year))
        except (TypeError, ValueError):
            continue
    return years


def get_aggregated_cards(limit: int = 5) -> List[Dict]:
    if _use_sqlalchemy_reads():
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

    with closing(get_conn()) as conn:
        total_indicators = conn.execute(
            "SELECT COUNT(DISTINCT indicator_name) FROM data_entries"
        ).fetchone()[0]

        total_rows = conn.execute(
            "SELECT COUNT(*) FROM data_entries"
        ).fetchone()[0]

        period_counts = conn.execute(
            """
            SELECT time_period, COUNT(*) as count
            FROM data_entries
            GROUP BY time_period
            ORDER BY time_period
            """
        ).fetchall()

    cards: List[Dict] = []

    cards.append(
        {
            "title": "Total Indicators",
            "value": total_indicators,
            "label": "Unique indicators in database",
        }
    )

    cards.append(
        {
            "title": "Total Data Rows",
            "value": total_rows,
            "label": "Total entries in database",
        }
    )

    period_labels = {
        "monthly": "Monthly Data",
        "quarterly": "Quarterly Data",
        "yearly": "Yearly Data",
    }

    for period in ["monthly", "quarterly", "yearly"]:
        count = 0
        for row in period_counts:
            if row["time_period"] == period:
                count = row["count"]
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
    if _use_sqlalchemy_reads():
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

    with closing(get_conn()) as conn:
        uploaders = conn.execute(
            "SELECT DISTINCT uploader_name FROM data_entries ORDER BY uploader_name"
        ).fetchall()
        uploader_list = [row["uploader_name"] for row in uploaders]

        indicators = conn.execute(
            "SELECT DISTINCT indicator_name FROM data_entries ORDER BY indicator_name"
        ).fetchall()
        indicator_list = [row["indicator_name"] for row in indicators]

        return {
            "uploaders": uploader_list,
            "indicators": indicator_list,
        }


def get_unique_indicators() -> List[str]:
    """Get list of unique indicators for plot filtering"""
    if _use_sqlalchemy_reads():
        try:
            session = get_session()
            return list(
                session.scalars(
                    select(DataEntry.indicator_name).distinct().order_by(DataEntry.indicator_name)
                ).all()
            )
        except SQLAlchemyError:
            return []

    with closing(get_conn()) as conn:
        indicators = conn.execute(
            "SELECT DISTINCT indicator_name FROM data_entries ORDER BY indicator_name"
        ).fetchall()
        return [row["indicator_name"] for row in indicators]
