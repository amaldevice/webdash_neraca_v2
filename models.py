import json
import os
import sqlite3
import re
from contextlib import closing
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from periods import parse_period_date

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

def _parse_period_filter_value(period_value: Optional[str]) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """Parse an input period value into (year, month, quarter)."""
    if not period_value:
        return None, None, None

    normalized = str(period_value).strip().upper()
    if not normalized:
        return None, None, None

    quarterly_match = re.fullmatch(r"^(\d{4})-Q([1-4])$", normalized)
    if quarterly_match:
        year = int(quarterly_match.group(1))
        quarter = int(quarterly_match.group(2))
        return year, None, quarter

    monthly_match = re.fullmatch(r"^(\d{4})-(\d{1,2})$", normalized)
    if monthly_match:
        year = int(monthly_match.group(1))
        month = int(monthly_match.group(2))
        if 1 <= month <= 12:
            return year, month, None
        return None, None, None

    year_match = re.fullmatch(r"^(\d{4})$", normalized)
    if year_match:
        return int(year_match.group(1)), None, None

    return None, None, None


def _period_index(year: Optional[int], month: Optional[int], quarter: Optional[int], is_start: bool) -> Optional[int]:
    """Convert a parsed period to a comparable month index (YYYYMM)."""
    if year is None:
        return None

    if month:
        return year * 100 + month

    if quarter:
        normalized_quarter = max(1, min(4, quarter))
        return year * 100 + ((normalized_quarter - 1) * 3 + (1 if is_start else 3))

    return year * 100 + (1 if is_start else 12)


def _apply_period_range_filter(
    clauses: List[str],
    params: List,
    time_period_filter: Optional[str],
    period_start: Optional[str],
    period_end: Optional[str],
) -> None:
    """Append period filter clauses (start/end) to query clauses and params."""
    start_year, start_month, start_quarter = _parse_period_filter_value(period_start)
    end_year, end_month, end_quarter = _parse_period_filter_value(period_end)

    if time_period_filter == "monthly":
        start_month = start_month or 1 if start_year else None
        end_month = end_month or 12 if end_year else None
        if start_year is not None and start_month is not None:
            clauses.append("(year > ? OR (year = ? AND COALESCE(month, 1) >= ?))")
            params.extend([start_year, start_year, start_month])
        if end_year is not None and end_month is not None:
            clauses.append("(year < ? OR (year = ? AND COALESCE(month, 12) <= ?))")
            params.extend([end_year, end_year, end_month])
        return

    if time_period_filter == "quarterly":
        start_quarter = start_quarter or 1 if start_year else None
        end_quarter = end_quarter or 4 if end_year else None
        if start_year is not None and start_quarter is not None:
            clauses.append("(year > ? OR (year = ? AND COALESCE(quarter, 1) >= ?))")
            params.extend([start_year, start_year, start_quarter])
        if end_year is not None and end_quarter is not None:
            clauses.append("(year < ? OR (year = ? AND COALESCE(quarter, 4) <= ?))")
            params.extend([end_year, end_year, end_quarter])
        return

    if time_period_filter == "yearly":
        if start_year is not None:
            clauses.append("year >= ?")
            params.append(start_year)
        if end_year is not None:
            clauses.append("year <= ?")
            params.append(end_year)
        return

    start_index = _period_index(start_year, start_month, start_quarter, is_start=True)
    end_index = _period_index(end_year, end_month, end_quarter, is_start=False)
    period_expression = "(year * 100 + COALESCE(month, COALESCE(quarter * 3, 1)))"
    if start_index is not None:
        clauses.append(f"{period_expression} >= ?")
        params.append(start_index)
    if end_index is not None:
        clauses.append(f"{period_expression} <= ?")
        params.append(end_index)


def get_total_entries_count(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> int:
    clauses = []
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

    _apply_period_range_filter(
        clauses=clauses,
        params=params,
        time_period_filter=time_period,
        period_start=period_start,
        period_end=period_end,
    )

    base_query = "SELECT COUNT(*) FROM data_entries"
    if clauses:
        base_query += " WHERE " + " AND ".join(clauses)

    with closing(get_conn()) as conn:
        row = conn.execute(base_query, tuple(params)).fetchone()
        return row[0] if row else 0


def query_data_entries(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    limit: int = 100,
    offset: Optional[int] = 0,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None
) -> List[Dict]:
    clauses = []
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

    _apply_period_range_filter(
        clauses=clauses,
        params=params,
        time_period_filter=time_period,
        period_start=period_start,
        period_end=period_end,
    )

    base_query = """
        SELECT id, uploader_name, version, indicator_name, value, data_type, time_period, created_at,
               year, month, quarter
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
            "quarter": row["quarter"],
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


def clear_all_data() -> bool:
    """Clear all data from database tables (for testing)"""
    try:
        with closing(get_conn()) as conn:
            conn.execute("DELETE FROM data_entries")
            conn.execute("DELETE FROM aggregated_summary")
            conn.commit()
            return True
    except Exception as e:
        print(f"Error clearing data: {e}")
        return False


def delete_data_by_filter(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None
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

    _apply_period_range_filter(
        clauses=clauses,
        params=params,
        time_period_filter=time_period,
        period_start=period_start,
        period_end=period_end,
    )

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


def calculate_period_comparisons(
    indicator: str,
    analysis_year: str = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> Dict:
    """Calculate period comparisons for an indicator (Q to Q, M to M, Y to Y, YTD, C to C)"""
    try:
        with closing(get_conn()) as conn:
            # Base query to get all data for the indicator
            base_query = """
                SELECT year, month, quarter, value, time_period, data_type
                FROM data_entries
                WHERE indicator_name = ? AND year IS NOT NULL
            """
            params: List = [indicator]
            if analysis_year:
                base_query += " AND year = ?"
                params.append(int(analysis_year))

            period_clauses: List[str] = []
            period_params: List = []
            _apply_period_range_filter(
                clauses=period_clauses,
                params=period_params,
                time_period_filter=None,
                period_start=period_start,
                period_end=period_end,
            )
            if period_clauses:
                base_query += " AND " + " AND ".join(period_clauses)
                params.extend(period_params)

            base_query += " ORDER BY year, month, quarter"
            rows = conn.execute(base_query, params).fetchall()

            if not rows:
                return {"error": "Tidak ada data untuk indikator ini"}

            # Convert to list of dicts
            data = []
            for row in rows:
                data.append({
                    'year': row['year'],
                    'month': row['month'],
                    'quarter': row['quarter'],
                    'value': row['value'],
                    'time_period': row['time_period'],
                    'data_type': row['data_type']
                })

            # Calculate different comparisons
            results = {
                'indicator': indicator,
                'analysis_year': analysis_year or 'All Years',
                'quarterly_comparison': calculate_quarterly_comparison(data),
                'monthly_comparison': calculate_monthly_comparison(data),
                'yearly_comparison': calculate_yearly_comparison(data),
                'ytd_comparison': calculate_ytd_comparison(data),
                'current_to_current': calculate_current_to_current(data)
            }

            return results

    except Exception as e:
        return {"error": f"Error calculating comparisons: {str(e)}"}


def calculate_quarterly_comparison(data):
    """Calculate Q to Q (Quarter to Quarter) comparison"""
    quarterly_data = {}

    # Group by year and quarter
    for item in data:
        if item['quarter'] is not None:
            key = f"{item['year']}-Q{item['quarter']}"
            if key not in quarterly_data:
                quarterly_data[key] = 0
            quarterly_data[key] += item['value']

    # Calculate Q to Q comparison
    quarters = sorted(quarterly_data.keys())
    comparison = []

    for i in range(1, len(quarters)):
        current_quarter = quarters[i]
        prev_quarter = quarters[i-1]
        current_value = quarterly_data[current_quarter]
        prev_value = quarterly_data[prev_quarter]

        if prev_value != 0:
            change = ((current_value - prev_value) / prev_value) * 100
            comparison.append({
                'period': current_quarter,
                'current_value': round(current_value, 2),
                'previous_value': round(prev_value, 2),
                'change_percent': round(change, 2),
                'change_type': 'increase' if change > 0 else 'decrease'
            })

    return comparison


def calculate_monthly_comparison(data):
    """Calculate M to M (Month to Month) comparison"""
    monthly_data = {}

    # Group by year and month
    for item in data:
        if item['month'] is not None:
            key = f"{item['year']}-{item['month']:02d}"
            if key not in monthly_data:
                monthly_data[key] = 0
            monthly_data[key] += item['value']

    # Calculate M to M comparison
    months = sorted(monthly_data.keys())
    comparison = []

    for i in range(1, len(months)):
        current_month = months[i]
        prev_month = months[i-1]
        current_value = monthly_data[current_month]
        prev_value = monthly_data[prev_month]

        if prev_value != 0:
            change = ((current_value - prev_value) / prev_value) * 100
            comparison.append({
                'period': current_month,
                'current_value': round(current_value, 2),
                'previous_value': round(prev_value, 2),
                'change_percent': round(change, 2),
                'change_type': 'increase' if change > 0 else 'decrease'
            })

    return comparison


def calculate_yearly_comparison(data):
    """Calculate Y to Y (Year to Year) comparison"""
    yearly_data = {}

    # Group by year
    for item in data:
        year = item['year']
        if year not in yearly_data:
            yearly_data[year] = 0
        yearly_data[year] += item['value']

    # Calculate Y to Y comparison
    years = sorted(yearly_data.keys())
    comparison = []

    for i in range(1, len(years)):
        current_year = years[i]
        prev_year = years[i-1]
        current_value = yearly_data[current_year]
        prev_value = yearly_data[prev_year]

        if prev_value != 0:
            change = ((current_value - prev_value) / prev_value) * 100
            comparison.append({
                'period': str(current_year),
                'current_value': round(current_value, 2),
                'previous_value': round(prev_value, 2),
                'change_percent': round(change, 2),
                'change_type': 'increase' if change > 0 else 'decrease'
            })

    return comparison


def calculate_ytd_comparison(data):
    """Calculate YTD (Year to Date) accumulation"""
    ytd_data = {}

    # Group by year and accumulate monthly/quarterly data
    for item in data:
        year = item['year']
        if year not in ytd_data:
            ytd_data[year] = {'monthly': {}, 'quarterly': {}}

        if item['month'] is not None:
            month_key = item['month']
            if month_key not in ytd_data[year]['monthly']:
                ytd_data[year]['monthly'][month_key] = 0
            ytd_data[year]['monthly'][month_key] += item['value']

        if item['quarter'] is not None:
            quarter_key = item['quarter']
            if quarter_key not in ytd_data[year]['quarterly']:
                ytd_data[year]['quarterly'][quarter_key] = 0
            ytd_data[year]['quarterly'][quarter_key] += item['value']

    # Calculate YTD accumulation for each year
    ytd_results = []
    for year, year_data in ytd_data.items():
        # Monthly YTD
        monthly_ytd = []
        cumulative = 0
        for month in sorted(year_data['monthly'].keys()):
            cumulative += year_data['monthly'][month]
            monthly_ytd.append({
                'period': f"{year}-{month:02d}",
                'ytd_value': round(cumulative, 2)
            })

        # Quarterly YTD
        quarterly_ytd = []
        cumulative = 0
        for quarter in sorted(year_data['quarterly'].keys()):
            cumulative += year_data['quarterly'][quarter]
            quarterly_ytd.append({
                'period': f"{year}-Q{quarter}",
                'ytd_value': round(cumulative, 2)
            })

        ytd_results.append({
            'year': year,
            'monthly_ytd': monthly_ytd,
            'quarterly_ytd': quarterly_ytd
        })

    return ytd_results


def calculate_current_to_current(data):
    """Calculate C to C (Current period vs same period last year)"""
    period_data = {}

    # Group by year and period (month or quarter)
    for item in data:
        year = item['year']
        if item['month'] is not None:
            period = f"M{item['month']:02d}"
        elif item['quarter'] is not None:
            period = f"Q{item['quarter']}"
        else:
            continue

        key = f"{year}-{period}"
        if key not in period_data:
            period_data[key] = 0
        period_data[key] += item['value']

    # Calculate current to current comparison
    comparison = []
    periods = sorted(period_data.keys())

    for current_period_key in periods:
        year, period = current_period_key.split('-')
        current_year = int(year)
        prev_year = current_year - 1
        prev_period_key = f"{prev_year}-{period}"

        if prev_period_key in period_data:
            current_value = period_data[current_period_key]
            prev_value = period_data[prev_period_key]

            if prev_value != 0:
                change = ((current_value - prev_value) / prev_value) * 100
                comparison.append({
                    'period': current_period_key,
                    'current_value': round(current_value, 2),
                    'previous_year_value': round(prev_value, 2),
                    'change_percent': round(change, 2),
                    'change_type': 'increase' if change > 0 else 'decrease'
                })

    return comparison


def insert_single_entry(
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    period_date: str,
    indicator: str,
    value: float
) -> bool:
    """Insert a single data entry"""
    try:
        # Parse period_date based on time_period (shared utility)
        year, month, quarter = parse_period_date(time_period, period_date)

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
                    year,  # parsed year
                    month,  # parsed month
                    quarter,  # parsed quarter
                    datetime.utcnow().isoformat()
                )
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False


def bulk_delete_entries(entry_ids: List[str]) -> int:
    """Delete multiple data entries by their IDs"""
    if not entry_ids:
        return 0

    try:
        with closing(get_conn()) as conn:
            # Create placeholders for SQL query
            placeholders = ','.join('?' * len(entry_ids))
            query = f"DELETE FROM data_entries WHERE id IN ({placeholders})"

            cursor = conn.execute(query, entry_ids)
            conn.commit()
            return cursor.rowcount
    except Exception:
        return 0


def bulk_update_entries(entry_ids: List[str], updates: Dict) -> int:
    """Update multiple data entries with the same values"""
    if not entry_ids or not updates:
        return 0

    try:
        with closing(get_conn()) as conn:
            # Build SET clause dynamically based on updates
            set_parts = []
            params = []

            for field, value in updates.items():
                if field in ['uploader_name', 'version', 'indicator_name', 'data_type', 'time_period']:
                    set_parts.append(f"{field} = ?")
                    params.append(value)
                elif field == 'value':
                    set_parts.append("value = ?")
                    params.append(float(value))

            if not set_parts:
                return 0

            set_clause = ", ".join(set_parts)

            # Create placeholders for WHERE IN clause
            placeholders = ','.join('?' * len(entry_ids))
            params.extend(entry_ids)

            query = f"UPDATE data_entries SET {set_clause} WHERE id IN ({placeholders})"

            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    except Exception:
        return 0