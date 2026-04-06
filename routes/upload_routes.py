# -*- coding: utf-8 -*-
"""Excel upload + manual entry routes."""
from __future__ import annotations

from flask import Flask, current_app, flash, redirect, render_template, request, session, url_for

from services.upload_flow import (
    MANUAL_ROUTE_MODE,
    UPLOAD_ROUTE_MODE,
    UPLOAD_TEMPLATE_NAME,
    collect_upload_file_errors,
    normalize_upload_action,
    parse_upload_form,
    process_manual_input_post,
    process_upload_confirm,
    process_upload_post_file,
    save_uploaded_excel,
    upload_folder_from_config,
)
from services.upload_preview import (
    cleanup_upload_preview_cache,
    delete_preview_session,
    load_preview_session,
    to_preview_context,
)


def _apply_upload_flow_response(resp):
    for msg, cat in resp.flashes:
        flash(msg, cat)
    if getattr(resp, "pop_upload_session_token", False):
        session.pop("upload_preview_token", None)
    if resp.kind == "redirect":
        return redirect(url_for("upload_data"))
    return render_template(
        UPLOAD_TEMPLATE_NAME,
        mode=UPLOAD_ROUTE_MODE,
        preview=resp.preview,
        upload_preview_token=resp.upload_preview_token,
        form_values=resp.form_values or {},
    )


def _apply_manual_flow_response(resp):
    for msg, cat in resp.flashes:
        flash(msg, cat)
    if resp.kind == "redirect":
        return redirect(url_for("manual_input"))
    return render_template(UPLOAD_TEMPLATE_NAME, mode=MANUAL_ROUTE_MODE)


def upload_data():
    upload_folder = upload_folder_from_config(current_app.config)
    cleanup_upload_preview_cache(upload_folder, session)
    preview_payload = None
    form_values: dict = {}
    if request.method == "GET" and request.args.get("clear_preview") == "1":
        old_token = session.get("upload_preview_token")
        if isinstance(old_token, str):
            session.pop("upload_preview_token", None)
            delete_preview_session(upload_folder, old_token)

    if request.method == "POST":
        form_values, action, preview_token, skip_dup = parse_upload_form(request.form)

        if action == "confirm":
            return _apply_upload_flow_response(
                process_upload_confirm(upload_folder, preview_token, form_values, skip_dup)
            )

        action = normalize_upload_action(action)
        file = request.files.get("excel_file")
        errors = collect_upload_file_errors(
            form_values["uploader"],
            form_values["version"],
            file,
            form_values["data_type"],
            form_values["time_period"],
        )
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                UPLOAD_TEMPLATE_NAME,
                mode=UPLOAD_ROUTE_MODE,
                preview=None,
                upload_preview_token=None,
                form_values=form_values,
            )

        destination, display_name, _stored = save_uploaded_excel(upload_folder, file)
        return _apply_upload_flow_response(
            process_upload_post_file(upload_folder, destination, display_name, form_values, action)
        )

    preview_token = session.get("upload_preview_token")
    payload = (
        load_preview_session(upload_folder, preview_token)
        if isinstance(preview_token, str)
        else None
    )
    if payload:
        meta = payload.get("metadata", {})
        form_values = {
            "uploader": meta.get("uploader", ""),
            "version": meta.get("version", ""),
            "data_type": meta.get("data_type", "flow"),
            "time_period": meta.get("time_period", "monthly"),
            "layout_override": payload.get("layout_override", "auto"),
        }
        preview_payload = to_preview_context(payload)

    return render_template(
        UPLOAD_TEMPLATE_NAME,
        mode=UPLOAD_ROUTE_MODE,
        preview=preview_payload,
        upload_preview_token=session.get("upload_preview_token"),
        form_values=form_values,
    )


def manual_input():
    if request.method == "POST":
        uploader = request.form.get("uploader", "").strip()
        version = request.form.get("version", "").strip()
        data_type = request.form.get("data_type", "flow").strip()
        time_period = request.form.get("time_period", "monthly").strip()
        period_date = request.form.get("period_date", "").strip()
        indicator = request.form.get("indicator", "").strip()
        value = request.form.get("value", "").strip()
        return _apply_manual_flow_response(
            process_manual_input_post(
                uploader, version, data_type, time_period, period_date, indicator, value
            )
        )

    return render_template(UPLOAD_TEMPLATE_NAME, mode=MANUAL_ROUTE_MODE)


def register(app: Flask) -> None:
    app.add_url_rule("/upload", endpoint="upload_data", view_func=upload_data, methods=["GET", "POST"])
    app.add_url_rule("/manual", endpoint="manual_input", view_func=manual_input, methods=["GET", "POST"])
