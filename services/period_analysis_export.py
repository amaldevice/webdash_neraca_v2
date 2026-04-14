# -*- coding: utf-8 -*-
"""HTTP export: parse form, run period analysis, return Excel attachment."""
from __future__ import annotations

import io
from datetime import datetime

from flask import Response

from services.audit_log import log_audit

from models import calculate_period_comparisons
from services.period_analysis_workbook import build_period_analysis_workbook
from services.request_params import get_period_range_params


def build_period_analysis_excel_response(
    form_data,
) -> tuple[Response | None, str | None]:
    """
    Parse POST form, run analysis, return (Response, None) or (None, flash_error).
    form_data: werkzeug ImmutableMultiDict or similar .get / getlist API.
    """
    indicator = form_data.get("indicator", "").strip()
    analysis_year = form_data.get("year", "").strip()
    period_start, period_end = get_period_range_params(
        form_data, start_key="period_start", end_key="end_period"
    )

    if not indicator:
        return None, "Pilih indikator terlebih dahulu."

    year_param = None
    if analysis_year and analysis_year.isdigit():
        year_param = int(analysis_year)

    results = calculate_period_comparisons(indicator, year_param, period_start, period_end)

    if "error" in results:
        log_audit(
            "period_analysis_export_rejected",
            indicator=indicator or None,
            reason=results.get("error"),
        )
        return None, results["error"]

    wb = build_period_analysis_workbook(indicator, results)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"BPS_Analysis_{indicator}_{timestamp}.xlsx"

    return (
        Response(
            output.getvalue(),
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
        ),
        None,
    )
