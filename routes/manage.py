# -*- coding: utf-8 -*-
"""Data management CRUD UI."""
from __future__ import annotations

from flask import Flask, flash, redirect, render_template, request, url_for

from models import get_filter_options
from services.data_management_actions import apply_data_management_post
from services.entry_list import (
    build_entry_list_page_bundle,
    parse_entry_list_params_and_pagination,
)


def data_management():
    list_params, page, limit, offset = parse_entry_list_params_and_pagination(
        request, filter_source="values"
    )

    if request.method == "POST":
        for msg, category in apply_data_management_post(request.form, **list_params.to_action_kwargs()):
            flash(msg, category)
        return redirect(url_for("data_management", **list_params.to_data_management_redirect_query()))

    entries, filters = build_entry_list_page_bundle(list_params, page, limit, offset)

    filter_options = get_filter_options()

    return render_template("data_management.html", entries=entries, filters=filters, filter_options=filter_options)


def register(app: Flask) -> None:
    app.add_url_rule(
        "/data-management",
        endpoint="data_management",
        view_func=data_management,
        methods=["GET", "POST"],
    )
