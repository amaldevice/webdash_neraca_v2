# -*- coding: utf-8 -*-
"""Excel upload + manual entry routes."""
from __future__ import annotations

from flask import Flask, Response, abort, current_app, flash, render_template, request, session

from routes.upload_response_adapter import (
    _dataset_wizard_template_kwargs,
    _ensure_upload_version,
    apply_manual_flow_response,
    apply_upload_flow_response,
)
from routes.upload_request_policy import evaluate_upload_csrf, evaluate_upload_rate_limit
from services.dataset_intake import resolve_dataset_for_intake
from services.template_service import build_template_file_response
from services.upload_flow import (
    MANUAL_ROUTE_MODE,
    UPLOAD_ROUTE_MODE,
    UPLOAD_TEMPLATE_NAME,
    process_manual_input_post,
    process_upload_confirm,
    process_upload_post_file,
    build_upload_response,
    upload_folder_from_config,
)
from services.upload_form import (
    collect_upload_file_errors,
    normalize_upload_action,
    parse_upload_form,
    save_uploaded_excel,
)
from services.upload_preview import (
    cleanup_upload_preview_cache,
    upload_page_preview_from_session,
)
from services.upload_preview_session_storage import file_backed_upload_preview_session_store


def _render_upload_template(
    *,
    preview: dict | None,
    upload_preview_token: str | None,
    form_values: dict | None = None,
) -> Response:
    from routes.upload_response_adapter import _render_upload_template as _adapter_render_upload

    return _adapter_render_upload(
        preview=preview,
        upload_preview_token=upload_preview_token,
        form_values=form_values,
    )


def upload_data():
    upload_folder = upload_folder_from_config(current_app.config)
    preview_store = file_backed_upload_preview_session_store(upload_folder)
    cleanup_upload_preview_cache(upload_folder, session)
    preview_payload = None
    form_values: dict = {}
    if request.method == "GET" and request.args.get("clear_preview") == "1":
        old_token = session.get("upload_preview_token")
        if isinstance(old_token, str):
            session.pop("upload_preview_token", None)
            preview_store.delete_session(old_token)

    require_dataset = bool(current_app.config.get("REQUIRE_DATASET_FOR_UPLOAD", False))

    if request.method == "POST":
        limit_decision = evaluate_upload_rate_limit()
        if not limit_decision.allowed:
            response = _render_upload_template(
                preview=None,
                upload_preview_token=session.get("upload_preview_token"),
                form_values={},
            )
            response.status_code = 429
            response.headers["Retry-After"] = str(limit_decision.window_seconds)
            response.headers["X-RateLimit-Limit"] = str(limit_decision.max_requests)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Window-Seconds"] = str(limit_decision.window_seconds)
            flash("Terlalu banyak unggahan dalam waktu singkat. Coba lagi nanti.", "error")
            return response

        normalized_form = _ensure_upload_version(request.form.to_dict())
        form_values, action, preview_token, skip_dup = parse_upload_form(normalized_form)
        if not evaluate_upload_csrf().allowed:
            response = apply_upload_flow_response(
                build_upload_response(
                    "render",
                    [("Token CSRF tidak valid. Kirim ulang form dengan token terbaru.", "error")],
                    preview=None,
                    upload_preview_token=preview_token or session.get("upload_preview_token"),
                    form_values=form_values,
                )
            )
            response.status_code = 400
            return response

        if action == "confirm":
            return apply_upload_flow_response(
                process_upload_confirm(
                    upload_folder,
                    preview_token,
                    form_values,
                    skip_dup,
                    require_dataset=require_dataset,
                )
            )

        action = normalize_upload_action(action)
        file = request.files.get("excel_file")
        slug = (form_values.get("dataset_slug") or "").strip()
        errors = collect_upload_file_errors(
            form_values["uploader"],
            form_values["version"],
            file,
            form_values["data_type"],
            form_values["time_period"],
            dataset_slug=slug or None,
            require_dataset=require_dataset,
        )
        if errors:
            for error in errors:
                flash(error, "error")
            return _render_upload_template(
                preview=None,
                upload_preview_token=None,
                form_values=form_values,
            )

        destination, display_name, _stored = save_uploaded_excel(upload_folder, file)
        return apply_upload_flow_response(
            process_upload_post_file(
                upload_folder,
                destination,
                display_name,
                form_values,
                action,
                require_dataset=require_dataset,
                old_token=session.get("upload_preview_token"),
            )
        )

    preview_token = session.get("upload_preview_token")
    payload = (
        preview_store.load_session(preview_token)
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
            "dataset_slug": (meta.get("dataset_slug") or "").strip(),
        }
        preview_payload = upload_page_preview_from_session(
            payload, upload_preview_token=preview_token
        )

    return _render_upload_template(
        preview=preview_payload,
        upload_preview_token=session.get("upload_preview_token"),
        form_values=form_values,
    )


def manual_input():
    if request.method == "POST":
        uploader = request.form.get("uploader", "").strip()
        version = _ensure_upload_version({"version": request.form.get("version", "").strip()}).get("version", "")
        data_type = request.form.get("data_type", "flow").strip()
        time_period = request.form.get("time_period", "monthly").strip()
        period_date = request.form.get("period_date", "").strip()
        indicator = request.form.get("indicator", "").strip()
        value = request.form.get("value", "").strip()
        confirm_duplicate = request.form.get("confirm_duplicate") == "1"
        dataset_slug = request.form.get("dataset_slug", "").strip()
        require_dataset = bool(current_app.config.get("REQUIRE_DATASET_FOR_UPLOAD", False))
        return apply_manual_flow_response(
            process_manual_input_post(
                uploader,
                version,
                data_type,
                time_period,
                period_date,
                indicator,
                value,
                confirm_duplicate=confirm_duplicate,
                dataset_slug=dataset_slug,
                require_dataset=require_dataset,
            )
        )

    ctx = _dataset_wizard_template_kwargs()
    return render_template(
        UPLOAD_TEMPLATE_NAME,
        mode=MANUAL_ROUTE_MODE,
        form_values=_ensure_upload_version({}),
        manual_duplicate=None,
        **ctx,
    )


def upload_dataset_template(dataset_slug: str) -> Response:
    slug = (dataset_slug or "").strip()
    if not slug or resolve_dataset_for_intake(slug).definition is None:
        abort(404)
    return build_template_file_response(slug)


def register(app: Flask) -> None:
    app.add_url_rule("/upload", endpoint="upload_data", view_func=upload_data, methods=["GET", "POST"])
    app.add_url_rule("/manual", endpoint="manual_input", view_func=manual_input, methods=["GET", "POST"])
    app.add_url_rule(
        "/upload/template/<dataset_slug>",
        endpoint="upload_dataset_template",
        view_func=upload_dataset_template,
        methods=["GET"],
    )
