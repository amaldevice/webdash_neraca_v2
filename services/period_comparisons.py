# -*- coding: utf-8 -*-
"""Load indicator rows from SQLite and assemble period comparison payloads."""
from __future__ import annotations

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
    from models.queries import fetch_series_for_comparison

    try:
        period_clauses: List[str] = []
        period_params: List = []
        apply_period_range_filter(
            clauses=period_clauses,
            params=period_params,
            time_period_filter=None,
            period_start=period_start,
            period_end=period_end,
        )
        data = fetch_series_for_comparison(indicator, analysis_year, period_clauses, period_params)

        if not data:
            return {"error": "Tidak ada data untuk indikator ini"}

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
