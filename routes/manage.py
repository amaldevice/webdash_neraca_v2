# -*- coding: utf-8 -*-
"""Data management CRUD UI and period-analysis Excel export."""
from __future__ import annotations

from flask import Flask, flash, redirect, render_template, request, url_for

from models import get_filter_options, get_total_entries_count, query_data_entries
from services.data_management_actions import apply_data_management_post
from services.list_view import (
    build_entries_filters_ui_dict,
    entries_query_kwargs,
    parse_entries_pagination,
)
from services.period_analysis_export import build_period_analysis_excel_response
from services.request_params import get_period_range_params, get_value_range_params


def data_management():
    filter_source = request.values
    data_type = filter_source.get("data_type", "")
    time_period = filter_source.get("time_period", "")
    uploader = filter_source.get("uploader", "")
    indicator = filter_source.get("indicator", "")
    period_start, period_end = get_period_range_params(filter_source)
    value_min, value_max = get_value_range_params(filter_source)

    page, limit, offset = parse_entries_pagination(request)

    if request.method == "POST":
        for msg, category in apply_data_management_post(
            request.form,
            data_type=data_type,
            time_period=time_period,
            uploader=uploader,
            indicator=indicator,
            period_start=period_start,
            period_end=period_end,
            value_min=value_min,
            value_max=value_max,
        ):
            flash(msg, category)
        return redirect(
            url_for(
                "data_management",
                data_type=data_type,
                time_period=time_period,
                uploader=uploader,
                indicator=indicator,
                start_period=period_start or "",
                end_period=period_end or "",
                value_min=value_min if value_min is not None else "",
                value_max=value_max if value_max is not None else "",
            )
        )

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

    return render_template("data_management.html", entries=entries, filters=filters, filter_options=filter_options)


def export_period_analysis_excel():
    response, err = build_period_analysis_excel_response(request.form)
    if err:
        flash(err, "error")
        return redirect(url_for("aggregated_summary"))
    return response


def register(app: Flask) -> None:
    app.add_url_rule(
        "/data-management",
        endpoint="data_management",
        view_func=data_management,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/export-period-analysis",
        endpoint="export_period_analysis_excel",
        view_func=export_period_analysis_excel,
        methods=["POST"],
    )
