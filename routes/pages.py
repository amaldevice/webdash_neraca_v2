# -*- coding: utf-8 -*-
"""Public pages: landing, preview, export, aggregated, chart/analysis JSON."""
from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from models import (
    calculate_period_comparisons,
    get_distinct_years,
    get_filter_options,
    get_total_entries_count,
    get_unique_indicators,
    query_data_entries,
)
from services.aggregation import fetch_aggregated_summary
from services.charts import generate_indicator_line_chart
from services.list_view import (
    build_entries_filters_ui_dict,
    entries_query_kwargs,
    parse_entries_pagination,
)
from services.audit_log import log_audit
from services.raw_export import build_raw_data_export_response
from services.request_params import get_period_range_params, get_value_range_params


def landing_page():
    summary = fetch_aggregated_summary()
    return render_template("landing.html", summary=summary)


def preview_data():
    data_type = request.args.get("data_type", "")
    time_period = request.args.get("time_period", "")
    uploader = request.args.get("uploader", "")
    indicator = request.args.get("indicator", "")
    period_start, period_end = get_period_range_params(request.args)
    value_min, value_max = get_value_range_params(request.args)

    page, limit, offset = parse_entries_pagination(request)

    summary = fetch_aggregated_summary()

    qkw = entries_query_kwargs(
        data_type,
        time_period,
        uploader,
        indicator,
        period_start,
        period_end,
        value_min,
        value_max,
    )
    entries = query_data_entries(**qkw, limit=limit, offset=offset)

    total_entries = get_total_entries_count(**qkw)

    filters = build_entries_filters_ui_dict(
        data_type=data_type,
        time_period=time_period,
        uploader=uploader,
        indicator=indicator,
        period_start=period_start,
        period_end=period_end,
        value_min=value_min,
        value_max=value_max,
        page=page,
        limit=limit,
        total_entries=total_entries,
    )

    filter_options = get_filter_options()

    return render_template(
        "preview.html", summary=summary, entries=entries, filters=filters, filter_options=filter_options
    )


def export_data():
    fmt = request.args.get("format", "csv").lower()
    data_type = request.args.get("data_type")
    time_period = request.args.get("time_period")
    uploader = request.args.get("uploader")
    indicator = request.args.get("indicator")
    period_start, period_end = get_period_range_params(request.args)
    value_min, value_max = get_value_range_params(request.args)
    qkw = entries_query_kwargs(
        data_type,
        time_period,
        uploader,
        indicator,
        period_start,
        period_end,
        value_min,
        value_max,
    )
    entries = query_data_entries(**qkw, limit=1000)
    log_audit(
        "raw_export",
        format=fmt,
        row_count=len(entries),
        data_type=data_type or None,
        time_period=time_period or None,
        has_uploader_filter=bool((uploader or "").strip()) if uploader is not None else False,
        has_indicator_filter=bool((indicator or "").strip()) if indicator is not None else False,
        has_period_range=bool(period_start or period_end),
        has_value_range=value_min is not None or value_max is not None,
    )
    return build_raw_data_export_response(entries, fmt)


def aggregated_summary():
    summary = fetch_aggregated_summary()
    indicators = get_unique_indicators()
    summary_dict = summary if isinstance(summary, dict) else {}
    available_years = summary_dict.get("available_years")
    if not isinstance(available_years, list) or not available_years:
        available_years = get_distinct_years()
    summary_with_indicators = dict(summary_dict)
    summary_with_indicators["indicators"] = indicators
    summary_with_indicators["available_years"] = available_years
    return render_template("aggregated.html", summary=summary_with_indicators)


def generate_plot():
    indicator = request.form.get("indicator_filter", "").strip()
    time_range = request.form.get("time_range", "all")
    period_start, period_end = get_period_range_params(
        request.form, start_key="period_start", end_key="period_end"
    )

    if not indicator:
        return jsonify({"error": "Pilih indikator terlebih dahulu"})

    if time_range == "all":
        range_start = None
        range_end = None
    else:
        normalized_year = time_range.strip()
        range_start = normalized_year
        range_end = normalized_year

    start_period = period_start or range_start
    end_period = period_end or range_end

    fig_json = generate_indicator_line_chart(indicator, time_range, start_period, end_period)
    return jsonify({"plot_json": fig_json})


def generate_period_analysis():
    indicator = request.form.get("indicator", "").strip()
    analysis_year = request.form.get("year", "").strip()
    period_start, period_end = get_period_range_params(
        request.form, start_key="period_start", end_key="end_period"
    )

    if not indicator:
        return jsonify({"error": "Pilih indikator terlebih dahulu"})

    results = calculate_period_comparisons(indicator, analysis_year or None, period_start, period_end)

    if "error" in results:
        return jsonify({"error": results["error"]})

    return jsonify({"analysis": results})


def register(app: Flask) -> None:
    app.add_url_rule("/", endpoint="landing_page", view_func=landing_page, methods=["GET"])
    app.add_url_rule("/preview-data", endpoint="preview_data", view_func=preview_data, methods=["GET"])
    app.add_url_rule("/export", endpoint="export_data", view_func=export_data, methods=["GET"])
    app.add_url_rule("/aggregated", endpoint="aggregated_summary", view_func=aggregated_summary, methods=["GET"])
    app.add_url_rule("/generate-plot", endpoint="generate_plot", view_func=generate_plot, methods=["POST"])
    app.add_url_rule(
        "/generate-period-analysis",
        endpoint="generate_period_analysis",
        view_func=generate_period_analysis,
        methods=["POST"],
    )
