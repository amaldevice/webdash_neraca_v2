from __future__ import annotations

from services.period_analysis_workbook import build_period_analysis_workbook


def _sample_results() -> dict:
    return {
        "analysis_year": 2024,
        "monthly_comparison": [
            {
                "period": "2024-01",
                "current_value": 120,
                "previous_value": 100,
                "change_percent": 20.0,
                "change_type": "increase",
            },
            {
                "period": "2024-02",
                "current_value": 90,
                "previous_value": 100,
                "change_percent": -10.0,
                "change_type": "decrease",
            },
        ],
        "quarterly_comparison": [
            {
                "period": "2024-Q1",
                "current_value": 300,
                "previous_value": 200,
                "change_percent": 50.0,
                "change_type": "increase",
            }
        ],
        "yearly_comparison": [
            {
                "period": "2024",
                "current_value": 1200,
                "previous_value": 1000,
                "change_percent": 20.0,
                "change_type": "increase",
            }
        ],
        "ytd_comparison": [
            {
                "year": 2024,
                "monthly_ytd": [
                    {"period": "01", "monthly_value": 10, "ytd_value": 10},
                    {"period": "02", "monthly_value": 20, "ytd_value": 30},
                ],
            }
        ],
        "current_to_current": [
            {
                "period": "2024-M02",
                "current_value": 90,
                "previous_year_value": 80,
                "change_percent": 12.5,
                "change_type": "increase",
            }
        ],
    }


def test_build_workbook_has_expected_sheets_and_order():
    wb = build_period_analysis_workbook("GDP", _sample_results())
    assert wb.sheetnames == ["Dashboard", "M to M", "Q ke Q", "Y ke Y", "YTD", "C ke C", "Metadata"]


def test_build_workbook_dashboard_and_metadata_content():
    wb = build_period_analysis_workbook("Inflasi", _sample_results())
    dashboard = wb["Dashboard"]
    metadata = wb["Metadata"]
    assert dashboard["A1"].value == "📊 Analisis Periode: Inflasi"
    assert dashboard["A4"].value == "📈 Ringkasan Data"
    assert dashboard["A6"].value == "M ke M (Bulanan)"
    assert dashboard["B6"].value == 2
    assert dashboard["C6"].value == "+5.00%"
    assert dashboard["D8"].value == "✓"
    assert metadata["A1"].value == "📋 Informasi Analisis"
    assert metadata["A3"].value == "Indikator"
    assert metadata["B3"].value == "Inflasi"
    assert metadata["A6"].value == "Jumlah Periode M-M"
    assert metadata["A7"].value == "Jumlah Periode Q-Q"


def test_build_workbook_without_comparison_sections_only_keeps_core_sheets():
    results = {
        "analysis_year": 2024,
        "monthly_comparison": [],
        "quarterly_comparison": [],
        "yearly_comparison": [],
        "ytd_comparison": [],
        "current_to_current": [],
    }
    wb = build_period_analysis_workbook("Nilai", results)
    assert wb.sheetnames == ["Dashboard", "Metadata"]
