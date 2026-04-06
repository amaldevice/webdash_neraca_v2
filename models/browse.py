# -*- coding: utf-8 -*-
from contextlib import closing
from typing import Dict, List

from .connection import get_conn


def get_latest_metadata() -> Dict[str, str]:
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

    cards.append({
        "title": "Total Indicators",
        "value": total_indicators,
        "label": "Unique indicators in database"
    })

    cards.append({
        "title": "Total Data Rows",
        "value": total_rows,
        "label": "Total entries in database"
    })

    period_labels = {
        "monthly": "Monthly Data",
        "quarterly": "Quarterly Data",
        "yearly": "Yearly Data"
    }

    for period in ["monthly", "quarterly", "yearly"]:
        count = 0
        for row in period_counts:
            if row["time_period"] == period:
                count = row["count"]
                break

        cards.append({
            "title": period_labels[period],
            "value": count,
            "label": f"Data points for {period} period"
        })

    if total_rows == 0:
        return [{"title": "Belum ada data", "value": 0, "label": "—"}]

    return cards[:limit]


def get_filter_options() -> Dict[str, List[str]]:
    """Get available options for filters (uploaders and indicators)"""
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
            "indicators": indicator_list
        }


def get_unique_indicators() -> List[str]:
    """Get list of unique indicators for plot filtering"""
    with closing(get_conn()) as conn:
        indicators = conn.execute(
            "SELECT DISTINCT indicator_name FROM data_entries ORDER BY indicator_name"
        ).fetchall()
        return [row["indicator_name"] for row in indicators]
