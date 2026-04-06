# -*- coding: utf-8 -*-
"""Load indicator rows from SQLite and assemble period comparison payloads."""
from __future__ import annotations

from contextlib import closing
from typing import Dict, List, Optional

from services.period_comparison_calculators import (
    calculate_current_to_current,
    calculate_monthly_comparison,
    calculate_quarterly_comparison,
    calculate_ytd_comparison,
    calculate_yearly_comparison,
)
from services.period_filters import apply_period_range_filter

# Re-export for `from services.period_comparisons import …` / models package
__all__ = [
    "calculate_current_to_current",
    "calculate_monthly_comparison",
    "calculate_period_comparisons",
    "calculate_quarterly_comparison",
    "calculate_ytd_comparison",
    "calculate_yearly_comparison",
]


def calculate_period_comparisons(
    indicator: str,
    analysis_year: str = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> Dict:
    """Calculate period comparisons for an indicator (Q to Q, M to M, Y to Y, YTD, C to C)."""
    from models import get_conn

    try:
        with closing(get_conn()) as conn:
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
            apply_period_range_filter(
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

            data = []
            for row in rows:
                data.append(
                    {
                        "year": row["year"],
                        "month": row["month"],
                        "quarter": row["quarter"],
                        "value": row["value"],
                        "time_period": row["time_period"],
                        "data_type": row["data_type"],
                    }
                )

            return {
                "indicator": indicator,
                "analysis_year": analysis_year or "All Years",
                "quarterly_comparison": calculate_quarterly_comparison(data),
                "monthly_comparison": calculate_monthly_comparison(data),
                "yearly_comparison": calculate_yearly_comparison(data),
                "ytd_comparison": calculate_ytd_comparison(data),
                "current_to_current": calculate_current_to_current(data),
            }

    except Exception as e:
        return {"error": f"Error calculating comparisons: {str(e)}"}
