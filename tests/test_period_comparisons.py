"""Unit tests for pure period comparison calculators (no DB)."""
from __future__ import annotations

from services.period_comparison_calculators import (
    calculate_current_to_current,
    calculate_monthly_comparison,
    calculate_quarterly_comparison,
    calculate_ytd_comparison,
    calculate_yearly_comparison,
    _calc_growth,
    _calc_percentage,
    _safe_divide,
)


def _row(year, month, quarter, value):
    return {
        "year": year,
        "month": month,
        "quarter": quarter,
        "value": value,
        "time_period": "monthly",
        "data_type": "flow",
    }


def _assert_dict_keys(row, expected_keys):
    assert list(row.keys()) == expected_keys


def test_safe_divide_zero_denominator():
    assert _safe_divide(10, 0) == 0.0


def test_safe_divide_returns_expected_ratio():
    assert _safe_divide(10, 2) == 5.0


def test_calc_growth_ratio():
    assert _calc_growth(150.0, 100.0) == 0.5


def test_calc_percentage_rounding():
    assert _calc_percentage(0.123456) == 12.35


def test_calculate_quarterly_comparison_sequence():
    data = [
        _row(2024, None, 1, 100.0),
        _row(2024, None, 2, 150.0),
    ]
    out = calculate_quarterly_comparison(data)
    assert len(out) == 1
    assert out[0]["period"] == "2024-Q2"
    assert out[0]["previous_value"] == 100.0
    assert out[0]["current_value"] == 150.0
    assert out[0]["change_percent"] == 50.0
    assert out[0]["change_type"] == "increase"


def test_calculate_quarterly_comparison_decrease():
    data = [
        _row(2024, None, 1, 200.0),
        _row(2024, None, 2, 100.0),
    ]
    out = calculate_quarterly_comparison(data)
    assert out[0]["change_type"] == "decrease"
    assert out[0]["change_percent"] == -50.0


def test_calculate_monthly_comparison():
    data = [
        _row(2024, 1, 1, 10.0),
        _row(2024, 2, 1, 30.0),
    ]
    out = calculate_monthly_comparison(data)
    assert len(out) == 1
    assert out[0]["period"] == "2024-02"
    assert out[0]["change_percent"] == 200.0


def test_calculate_yearly_comparison():
    data = [
        _row(2023, 6, 2, 50.0),
        _row(2024, 6, 2, 75.0),
    ]
    out = calculate_yearly_comparison(data)
    assert len(out) == 1
    assert out[0]["period"] == "2024"
    assert out[0]["change_percent"] == 50.0


def test_calculate_ytd_monthly_accumulation():
    data = [
        _row(2024, 1, 1, 10.0),
        _row(2024, 2, 1, 15.0),
    ]
    out = calculate_ytd_comparison(data)
    assert len(out) == 1
    block = out[0]
    assert block["year"] == 2024
    assert len(block["monthly_ytd"]) == 2
    assert block["monthly_ytd"][0]["ytd_value"] == 10.0
    assert block["monthly_ytd"][1]["ytd_value"] == 25.0


def test_calculate_current_to_current_month_yoy():
    data = [
        _row(2023, 3, 1, 100.0),
        _row(2024, 3, 1, 110.0),
    ]
    out = calculate_current_to_current(data)
    assert len(out) == 1
    assert out[0]["period"] == "2024-M03"
    assert out[0]["previous_year_value"] == 100.0
    assert out[0]["current_value"] == 110.0
    assert out[0]["change_percent"] == 10.0


def test_calculate_current_to_current_quarter_yoy():
    data = [
        _row(2023, None, 2, 40.0),
        _row(2024, None, 2, 20.0),
    ]
    out = calculate_current_to_current(data)
    assert len(out) == 1
    assert "Q2" in out[0]["period"]
    assert out[0]["change_type"] == "decrease"


def test_indicator_output_key_order():
    quarterly = calculate_quarterly_comparison(
        [
            _row(2024, None, 1, 100.0),
            _row(2024, None, 2, 110.0),
        ]
    )
    monthly = calculate_monthly_comparison(
        [_row(2024, 1, 1, 10.0), _row(2024, 2, 1, 11.0)]
    )
    yearly = calculate_yearly_comparison(
        [_row(2023, 6, 2, 5.0), _row(2024, 6, 2, 10.0)]
    )
    current = calculate_current_to_current(
        [_row(2023, 3, 1, 10.0), _row(2024, 3, 1, 20.0)]
    )
    ytd = calculate_ytd_comparison([_row(2024, 1, 1, 10.0), _row(2024, 2, 2, 20.0)])

    assert len(quarterly) == 1
    assert len(monthly) == 1
    assert len(yearly) == 1
    assert len(current) == 1
    assert len(ytd) == 1

    _assert_dict_keys(
        quarterly[0], ["period", "current_value", "previous_value", "change_percent", "change_type"]
    )
    _assert_dict_keys(
        monthly[0], ["period", "current_value", "previous_value", "change_percent", "change_type"]
    )
    _assert_dict_keys(
        yearly[0], ["period", "current_value", "previous_value", "change_percent", "change_type"]
    )
    _assert_dict_keys(
        current[0],
        ["period", "current_value", "previous_year_value", "change_percent", "change_type"],
    )
    _assert_dict_keys(ytd[0], ["year", "monthly_ytd", "quarterly_ytd"])
    _assert_dict_keys(ytd[0]["monthly_ytd"][0], ["period", "ytd_value"])
    _assert_dict_keys(ytd[0]["quarterly_ytd"][0], ["period", "ytd_value"])
