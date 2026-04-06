# -*- coding: utf-8 -*-
"""Pure period-over-period math (Q/Q, M/M, Y/Y, YTD, same period YoY). Used by `period_comparisons`."""
from __future__ import annotations


def _safe_divide(numerator: float, denominator: float) -> float:
    """Return a safe ratio, avoiding division by zero."""
    if denominator == 0:
        return 0.0

    return numerator / denominator


def _calc_growth(current_value: float, previous_value: float) -> float:
    """Calculate growth ratio against a previous period."""
    return _safe_divide(current_value - previous_value, previous_value)


def _calc_percentage(value: float) -> float:
    """Convert a growth ratio to rounded percentage points."""
    return round(value * 100, 2)


def calculate_quarterly_comparison(data):
    """Calculate Q to Q (Quarter to Quarter) comparison."""
    quarterly_data = {}

    for item in data:
        if item["quarter"] is not None:
            key = f"{item['year']}-Q{item['quarter']}"
            if key not in quarterly_data:
                quarterly_data[key] = 0
            quarterly_data[key] += item["value"]

    quarters = sorted(quarterly_data.keys())
    comparison = []

    for i in range(1, len(quarters)):
        current_quarter = quarters[i]
        prev_quarter = quarters[i - 1]
        current_value = quarterly_data[current_quarter]
        prev_value = quarterly_data[prev_quarter]

        if prev_value != 0:
            change = _calc_percentage(_calc_growth(current_value, prev_value))
            comparison.append(
                {
                    "period": current_quarter,
                    "current_value": round(current_value, 2),
                    "previous_value": round(prev_value, 2),
                    "change_percent": round(change, 2),
                    "change_type": "increase" if change > 0 else "decrease",
                }
            )

    return comparison


def calculate_monthly_comparison(data):
    """Calculate M to M (Month to Month) comparison."""
    monthly_data = {}

    for item in data:
        if item["month"] is not None:
            key = f"{item['year']}-{item['month']:02d}"
            if key not in monthly_data:
                monthly_data[key] = 0
            monthly_data[key] += item["value"]

    months = sorted(monthly_data.keys())
    comparison = []

    for i in range(1, len(months)):
        current_month = months[i]
        prev_month = months[i - 1]
        current_value = monthly_data[current_month]
        prev_value = monthly_data[prev_month]

        if prev_value != 0:
            change = _calc_percentage(_calc_growth(current_value, prev_value))
            comparison.append(
                {
                    "period": current_month,
                    "current_value": round(current_value, 2),
                    "previous_value": round(prev_value, 2),
                    "change_percent": round(change, 2),
                    "change_type": "increase" if change > 0 else "decrease",
                }
            )

    return comparison


def calculate_yearly_comparison(data):
    """Calculate Y to Y (Year to Year) comparison."""
    yearly_data = {}

    for item in data:
        year = item["year"]
        if year not in yearly_data:
            yearly_data[year] = 0
        yearly_data[year] += item["value"]

    years = sorted(yearly_data.keys())
    comparison = []

    for i in range(1, len(years)):
        current_year = years[i]
        prev_year = years[i - 1]
        current_value = yearly_data[current_year]
        prev_value = yearly_data[prev_year]

        if prev_value != 0:
            change = _calc_percentage(_calc_growth(current_value, prev_value))
            comparison.append(
                {
                    "period": str(current_year),
                    "current_value": round(current_value, 2),
                    "previous_value": round(prev_value, 2),
                    "change_percent": round(change, 2),
                    "change_type": "increase" if change > 0 else "decrease",
                }
            )

    return comparison


def calculate_ytd_comparison(data):
    """Calculate YTD (Year to Date) accumulation."""
    ytd_data = {}

    for item in data:
        year = item["year"]
        if year not in ytd_data:
            ytd_data[year] = {"monthly": {}, "quarterly": {}}

        if item["month"] is not None:
            month_key = item["month"]
            if month_key not in ytd_data[year]["monthly"]:
                ytd_data[year]["monthly"][month_key] = 0
            ytd_data[year]["monthly"][month_key] += item["value"]

        if item["quarter"] is not None:
            quarter_key = item["quarter"]
            if quarter_key not in ytd_data[year]["quarterly"]:
                ytd_data[year]["quarterly"][quarter_key] = 0
            ytd_data[year]["quarterly"][quarter_key] += item["value"]

    ytd_results = []
    for year, year_data in ytd_data.items():
        monthly_ytd = []
        cumulative = 0
        for month in sorted(year_data["monthly"].keys()):
            cumulative += year_data["monthly"][month]
            monthly_ytd.append(
                {
                    "period": f"{year}-{month:02d}",
                    "ytd_value": round(cumulative, 2),
                }
            )

        quarterly_ytd = []
        cumulative = 0
        for quarter in sorted(year_data["quarterly"].keys()):
            cumulative += year_data["quarterly"][quarter]
            quarterly_ytd.append(
                {
                    "period": f"{year}-Q{quarter}",
                    "ytd_value": round(cumulative, 2),
                }
            )

        ytd_results.append(
            {
                "year": year,
                "monthly_ytd": monthly_ytd,
                "quarterly_ytd": quarterly_ytd,
            }
        )

    return ytd_results


def calculate_current_to_current(data):
    """Calculate C to C (Current period vs same period last year)."""
    period_data = {}

    for item in data:
        year = item["year"]
        if item["month"] is not None:
            period = f"M{item['month']:02d}"
        elif item["quarter"] is not None:
            period = f"Q{item['quarter']}"
        else:
            continue

        key = f"{year}-{period}"
        if key not in period_data:
            period_data[key] = 0
        period_data[key] += item["value"]

    comparison = []
    periods = sorted(period_data.keys())

    for current_period_key in periods:
        year, period = current_period_key.split("-")
        current_year = int(year)
        prev_year = current_year - 1
        prev_period_key = f"{prev_year}-{period}"

        if prev_period_key in period_data:
            current_value = period_data[current_period_key]
            prev_value = period_data[prev_period_key]

            if prev_value != 0:
                change = _calc_percentage(_calc_growth(current_value, prev_value))
                comparison.append(
                    {
                        "period": current_period_key,
                        "current_value": round(current_value, 2),
                        "previous_year_value": round(prev_value, 2),
                        "change_percent": round(change, 2),
                        "change_type": "increase" if change > 0 else "decrease",
                    }
                )

    return comparison
