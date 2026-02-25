import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Dict, Iterable, List, Optional

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader_name TEXT NOT NULL,
                version TEXT NOT NULL,
                template_type TEXT,
                data_type TEXT,
                time_period TEXT,
                indicator_name TEXT NOT NULL,
                value REAL,
                unit TEXT,
                region_code TEXT,
                year INTEGER,
                month INTEGER,
                quarter INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_data_entry_variant
            ON data_entries(uploader_name, version, indicator_name, year, month, quarter);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS aggregated_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _to_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def insert_entries(entries: Iterable[Dict]) -> None:
    now = datetime.utcnow().isoformat()
    with closing(get_conn()) as conn:
        cursor = conn.cursor()
        for entry in entries:
            cursor.execute(
                """
                INSERT INTO data_entries (
                    uploader_name, version, template_type, data_type, time_period,
                    indicator_name, value, unit, region_code, year, month, quarter, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["uploader_name"],
                    entry["version"],
                    entry.get("template_type"),
                    entry.get("data_type"),
                    entry.get("time_period"),
                    entry["indicator_name"],
                    _to_float(entry.get("value")),
                    entry.get("unit"),
                    entry.get("region_code"),
                    entry.get("year"),
                    entry.get("month"),
                    entry.get("quarter"),
                    entry.get("created_at", now),
                ),
            )
        conn.commit()


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


def get_aggregated_cards(limit: int = 5) -> List[Dict]:
    with closing(get_conn()) as conn:
        # Get total indicators count
        total_indicators = conn.execute(
            "SELECT COUNT(DISTINCT indicator_name) FROM data_entries"
        ).fetchone()[0]

        # Get total rows count
        total_rows = conn.execute(
            "SELECT COUNT(*) FROM data_entries"
        ).fetchone()[0]

        # Get count by time period
        period_counts = conn.execute(
            """
            SELECT time_period, COUNT(*) as count
            FROM data_entries
            GROUP BY time_period
            ORDER BY time_period
            """
        ).fetchall()

        # Get latest timestamp
        latest_timestamp = conn.execute(
            "SELECT MAX(created_at) FROM data_entries"
        ).fetchone()[0]

    cards: List[Dict] = []

    # Total Indicators card
    cards.append({
        "title": "Total Indicators",
        "value": total_indicators,
        "label": "Unique indicators in database"
    })

    # Total Rows card
    cards.append({
        "title": "Total Data Rows",
        "value": total_rows,
        "label": "Total entries in database"
    })

    # Period-specific cards
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

    # If no data at all
    if total_rows == 0:
        return [{"title": "Belum ada data", "value": 0, "label": "—"}]

    return cards[:limit]


def get_total_entries_count(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
) -> int:
    clauses = []
    params: List = []
    if data_type:
        clauses.append("LOWER(data_type) = LOWER(?)")
        params.append(data_type)
    if time_period:
        clauses.append("LOWER(time_period) = LOWER(?)")
        params.append(time_period)

    base_query = "SELECT COUNT(*) FROM data_entries"
    if clauses:
        base_query += " WHERE " + " AND ".join(clauses)

    with closing(get_conn()) as conn:
        row = conn.execute(base_query, tuple(params)).fetchone()
        return row[0] if row else 0


def query_data_entries(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    limit: int = 100,
    offset: Optional[int] = 0,
) -> List[Dict]:
    clauses = []
    params: List = []
    if data_type:
        clauses.append("LOWER(data_type) = LOWER(?)")
        params.append(data_type)
    if time_period:
        clauses.append("LOWER(time_period) = LOWER(?)")
        params.append(time_period)

    base_query = """
        SELECT id, uploader_name, version, indicator_name, value, data_type, time_period, created_at,
               year, month
        FROM data_entries
    """
    if clauses:
        base_query += " WHERE " + " AND ".join(clauses)
    base_query += " ORDER BY datetime(created_at) DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(get_conn()) as conn:
        rows = conn.execute(base_query, tuple(params)).fetchall()

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
            "tanggal_data": f"{row['year']}-{row['month']:02d}" if row["year"] and row["month"] else "N/A",
        }
        for row in rows
    ]


def save_aggregated_summary(summary: Dict) -> None:
    payload = json.dumps(summary, ensure_ascii=False)
    now = datetime.utcnow().isoformat()
    with closing(get_conn()) as conn:
        conn.execute("DELETE FROM aggregated_summary")
        conn.execute(
            """
            INSERT INTO aggregated_summary (summary_json, updated_at)
            VALUES (?, ?)
            """,
            (payload, now),
        )
        conn.commit()


def load_cached_summary() -> Optional[Dict]:
    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT summary_json FROM aggregated_summary
            ORDER BY datetime(updated_at) DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        return json.loads(row["summary_json"])


def get_filter_options() -> Dict[str, List[str]]:
    """Get available options for filters (uploaders and indicators)"""
    with closing(get_conn()) as conn:
        # Get unique uploaders
        uploaders = conn.execute(
            "SELECT DISTINCT uploader_name FROM data_entries ORDER BY uploader_name"
        ).fetchall()
        uploader_list = [row["uploader_name"] for row in uploaders]

        # Get unique indicators
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


def delete_data_entry(entry_id: str) -> bool:
    """Delete a single data entry by ID"""
    try:
        with closing(get_conn()) as conn:
            cursor = conn.execute("DELETE FROM data_entries WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False


def delete_data_by_filter(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None
) -> int:
    """Delete data entries based on filters"""
    clauses = []
    params = []

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

    if not clauses:
        return 0  # Don't delete everything if no filters

    query = "DELETE FROM data_entries WHERE " + " AND ".join(clauses)

    with closing(get_conn()) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount


def update_data_entry(entry_id: str, new_value: float) -> bool:
    """Update the value of a data entry"""
    try:
        with closing(get_conn()) as conn:
            cursor = conn.execute(
                "UPDATE data_entries SET value = ? WHERE id = ?",
                (new_value, entry_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False


def update_data_entry_full(entry_id: str, data: Dict) -> bool:
    """Update all fields of a data entry"""
    try:
        with closing(get_conn()) as conn:
            cursor = conn.execute(
                """
                UPDATE data_entries SET
                    uploader_name = ?,
                    version = ?,
                    indicator_name = ?,
                    value = ?,
                    data_type = ?,
                    time_period = ?
                WHERE id = ?
                """,
                (
                    data["uploader_name"],
                    data["version"],
                    data["indicator_name"],
                    data["value"],
                    data["data_type"],
                    data["time_period"],
                    entry_id
                )
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False


def insert_single_entry(
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    indicator: str,
    value: float
) -> bool:
    """Insert a single data entry"""
    try:
        with closing(get_conn()) as conn:
            cursor = conn.execute(
                """
                INSERT INTO data_entries (
                    uploader_name, version, template_type, data_type, time_period,
                    indicator_name, value, unit, region_code, year, month, quarter, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uploader,
                    version,
                    "manual_crud",
                    data_type.lower() or "flow",
                    time_period.lower() or "monthly",
                    indicator,
                    value,
                    None,  # unit
                    None,  # region_code
                    None,  # year (will be parsed from period if needed)
                    None,  # month
                    None,  # quarter
                    datetime.utcnow().isoformat()
                )
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False