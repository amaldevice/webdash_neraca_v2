# -*- coding: utf-8 -*-
"""Public pages: landing, preview, export."""
from __future__ import annotations

from flask import Flask, render_template, request

from models import get_filter_options, get_landing_summary
from models.repositories.entry_list import count_entries_for_list, fetch_entries_for_list
from services.list_view import (
    EntryListParams,
    build_entries_filters_ui_dict,
    parse_entries_pagination,
)
from services.raw_export import build_raw_data_export_response
from services.request_params import get_period_range_params, get_value_range_params


def landing_page():
    landing_summary = get_landing_summary()
    return render_template("landing.html", landing_summary=landing_summary)


def preview_data():
    data_type = request.args.get("data_type", "")
    time_period = request.args.get("time_period", "")
    uploader = request.args.get("uploader", "")
    indicator = request.args.get("indicator", "")
    dataset_code = request.args.get("dataset_code", "")
    period_start, period_end = get_period_range_params(request.args)
    value_min, value_max = get_value_range_params(request.args)

    page, limit, offset = parse_entries_pagination(request)

    list_params = EntryListParams.from_request_strings(
        data_type=data_type,
        time_period=time_period,
        uploader=uploader,
        indicator=indicator,
        period_start=period_start,
        period_end=period_end,
        value_min=value_min,
        value_max=value_max,
        dataset_code=dataset_code,
    )
    qkw = list_params.to_query_kwargs()
    entries = fetch_entries_for_list(limit=limit, offset=offset, filters=qkw)

    total_entries = count_entries_for_list(qkw)

    filters = build_entries_filters_ui_dict(
        **list_params.to_ui_strings(),
        page=page,
        limit=limit,
        total_entries=total_entries,
    )

    filter_options = get_filter_options()

    return render_template(
        "preview.html", entries=entries, filters=filters, filter_options=filter_options
    )


def export_data():
    fmt = request.args.get("format", "csv").lower()
    data_type = request.args.get("data_type")
    time_period = request.args.get("time_period")
    uploader = request.args.get("uploader")
    indicator = request.args.get("indicator")
    dataset_code = request.args.get("dataset_code", "")
    period_start, period_end = get_period_range_params(request.args)
    value_min, value_max = get_value_range_params(request.args)
    list_params = EntryListParams.from_request_strings(
        data_type=data_type or "",
        time_period=time_period or "",
        uploader=uploader or "",
        indicator=indicator or "",
        period_start=period_start,
        period_end=period_end,
        value_min=value_min,
        value_max=value_max,
        dataset_code=dataset_code or "",
    )
    entries = fetch_entries_for_list(limit=1000, offset=0, filters=list_params.to_query_kwargs())
    return build_raw_data_export_response(entries, fmt)


def register(app: Flask) -> None:
    app.add_url_rule("/", endpoint="landing_page", view_func=landing_page, methods=["GET"])
    app.add_url_rule("/preview-data", endpoint="preview_data", view_func=preview_data, methods=["GET"])
    app.add_url_rule("/export", endpoint="export_data", view_func=export_data, methods=["GET"])
