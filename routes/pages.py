# -*- coding: utf-8 -*-
"""Public pages: landing, preview, export."""
from __future__ import annotations

from flask import Flask, render_template, request

from models import get_filter_options, get_landing_summary
from services.entry_list_page import (
    build_entry_list_page_bundle,
    fetch_entries_for_export,
    parse_entry_list_params_and_pagination,
)
from services.raw_export import build_raw_data_export_response


def landing_page():
    landing_summary = get_landing_summary()
    return render_template("landing.html", landing_summary=landing_summary)


def preview_data():
    list_params, page, limit, offset = parse_entry_list_params_and_pagination(
        request, filter_source="args"
    )
    entries, filters = build_entry_list_page_bundle(list_params, page, limit, offset)

    filter_options = get_filter_options()

    return render_template(
        "preview.html", entries=entries, filters=filters, filter_options=filter_options
    )


def export_data():
    fmt = request.args.get("format", "csv").lower()
    entries = fetch_entries_for_export(request)
    return build_raw_data_export_response(entries, fmt)


def register(app: Flask) -> None:
    app.add_url_rule("/", endpoint="landing_page", view_func=landing_page, methods=["GET"])
    app.add_url_rule("/preview-data", endpoint="preview_data", view_func=preview_data, methods=["GET"])
    app.add_url_rule("/export", endpoint="export_data", view_func=export_data, methods=["GET"])
