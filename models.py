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
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
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


def calculate_period_comparisons(indicator: str, analysis_year: str = None) -> Dict:
    """Calculate period comparisons for an indicator (Q to Q, M to M, Y to Y, YTD, C to C)"""
    try:
        with closing(get_conn()) as conn:
            # Base query to get all data for the indicator
            base_query = """
                SELECT year, month, quarter, value, time_period, data_type
                FROM data_entries
                WHERE indicator_name = ? AND year IS NOT NULL
            """

            params = [indicator]

            if analysis_year:
                base_query += " AND year = ?"
                params.append(int(analysis_year))

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
        # Parse period_date based on time_period
        year, month, quarter = _parse_period_date(time_period, period_date)

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


def _parse_period_date(time_period: str, period_date: str) -> tuple[int | None, int | None, int | None]:
    """Parse period_date string into year, month, quarter based on time_period format."""
    try:
        if time_period.lower() == 'monthly':
            # Format: YYYY-MM
            if '-' in period_date and len(period_date.split('-')) == 2:
                year_str, month_str = period_date.split('-')
                year = int(year_str)
                month = int(month_str)
                quarter = (month - 1) // 3 + 1  # Calculate quarter from month
                return year, month, quarter
        elif time_period.lower() == 'quarterly':
            # Format: YYYY-Q1/Q2/Q3/Q4
            if '-Q' in period_date:
                year_str, quarter_str = period_date.split('-Q')
                year = int(year_str)
                quarter = int(quarter_str)
                return year, None, quarter
        elif time_period.lower() == 'yearly':
            # Format: YYYY
            year = int(period_date)
            return year, None, None
    except (ValueError, IndexError):
        pass

    return None, None, None


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