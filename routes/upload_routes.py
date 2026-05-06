# -*- coding: utf-8 -*-
"""Excel upload + manual entry routes."""
from __future__ import annotations

from collections import defaultdict, deque
import secrets
import threading
import time
from flask import Flask, Response, abort, current_app, flash, make_response, redirect, render_template, request, session, url_for

from services.dataset_catalog import datasets_for_template_context, get_dataset_or_none
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
    delete_preview_session,
    load_preview_session,
    to_preview_context,
)
from services.timeutil import wita_now_iso


_UPLOAD_RATE_LIMIT_LOCK = threading.Lock()
_UPLOAD_RATE_LIMIT_STATE: dict[str, deque[float]] = defaultdict(deque)


def _dataset_wizard_template_kwargs() -> dict:
    """Katalog dataset + flag legacy / ketat untuk template upload & manual."""
    req = bool(current_app.config.get("REQUIRE_DATASET_FOR_UPLOAD", False))
    return {
        "datasets": datasets_for_template_context(),
        "legacy_dataset_choice_allowed": not req,
        "require_dataset_upload": req,
        "require_dataset_manual": req,
    }


def _upload_csrf_token() -> str:
    """Read-or-create CSRF token bound to session."""
    token = session.get("_upload_csrf_token")
    if not isinstance(token, str) or not token:
        token = secrets.token_urlsafe(32)
        session["_upload_csrf_token"] = token
    return token


def _validate_upload_csrf_token() -> bool:
    expected = session.get("_upload_csrf_token")
    provided = request.form.get("csrf_token", "")
    if not expected or not provided:
        return False
    return secrets.compare_digest(str(expected), str(provided))


def _upload_client_key() -> str:
    client_key = session.get("_upload_client_id")
    if not isinstance(client_key, str) or not client_key.strip():
        client_key = secrets.token_urlsafe(16)
        session["_upload_client_id"] = client_key
    return client_key


def _ensure_upload_version(form_values: dict | None) -> dict[str, str]:
    values = dict(form_values or {})
    values.setdefault("version", wita_now_iso())
    values.setdefault("dataset_slug", "")
    return values


def _upload_is_rate_limited() -> tuple[bool, int, int]:
    max_requests = int(current_app.config.get("UPLOAD_RATE_LIMIT_MAX_REQUESTS", 0))
    window_seconds = int(current_app.config.get("UPLOAD_RATE_LIMIT_WINDOW_SECONDS", 60))
    if max_requests <= 0:
        return False, max_requests, window_seconds

    key = _upload_client_key()
    now = time.monotonic()
    with _UPLOAD_RATE_LIMIT_LOCK:
        bucket = _UPLOAD_RATE_LIMIT_STATE[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= max_requests:
            return True, 0, window_seconds
        bucket.append(now)
        return False, max_requests - len(bucket), window_seconds


def _render_upload_template(
    *,
    preview: dict | None,
    upload_preview_token: str | None,
    form_values: dict | None = None,
) -> Response:
    form_values = _ensure_upload_version(form_values)
    ctx = _dataset_wizard_template_kwargs()
    return make_response(
        render_template(
            UPLOAD_TEMPLATE_NAME,
            mode=UPLOAD_ROUTE_MODE,
            preview=preview,
            upload_preview_token=upload_preview_token,
            form_values=form_values,
            upload_csrf_token=_upload_csrf_token(),
            **ctx,
        )
    )

def _apply_upload_flow_response(resp):
    for msg, cat in resp.flashes:
        flash(msg, cat)
    if getattr(resp, "pop_upload_session_token", False):
        session.pop("upload_preview_token", None)
    if resp.kind == "redirect":
        return redirect(url_for("upload_data"))
    return _render_upload_template(
        preview=resp.preview,
        upload_preview_token=resp.upload_preview_token,
        form_values=resp.form_values,
    )


def _apply_manual_flow_response(resp):
    for msg, cat in resp.flashes:
        flash(msg, cat)
    if resp.kind == "redirect":
        return redirect(url_for("manual_input"))
    ctx = _dataset_wizard_template_kwargs()
    return render_template(
        UPLOAD_TEMPLATE_NAME,
        mode=MANUAL_ROUTE_MODE,
        form_values=_ensure_upload_version(resp.form_values),
        manual_duplicate=resp.manual_duplicate,
        **ctx,
    )


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

    require_dataset = bool(current_app.config.get("REQUIRE_DATASET_FOR_UPLOAD", False))

    if request.method == "POST":
        if request.path == "/upload":
            is_rate_limited, _, window_seconds = _upload_is_rate_limited()
            if is_rate_limited:
                response = _render_upload_template(
                    preview=None,
                    upload_preview_token=session.get("upload_preview_token"),
                    form_values={},
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(window_seconds)
                response.headers["X-RateLimit-Limit"] = str(
                    current_app.config.get("UPLOAD_RATE_LIMIT_MAX_REQUESTS", 0)
                )
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Window-Seconds"] = str(window_seconds)
                flash("Terlalu banyak unggahan dalam waktu singkat. Coba lagi nanti.", "error")
                return response

        normalized_form = _ensure_upload_version(request.form.to_dict())
        form_values, action, preview_token, skip_dup = parse_upload_form(normalized_form)
        if not _validate_upload_csrf_token():
            response = _apply_upload_flow_response(
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
            return _apply_upload_flow_response(
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
        return _apply_upload_flow_response(
            process_upload_post_file(
                upload_folder,
                destination,
                display_name,
                form_values,
                action,
                require_dataset=require_dataset,
            )
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
            "dataset_slug": (meta.get("dataset_slug") or "").strip(),
        }
        preview_payload = to_preview_context(payload)

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
        return _apply_manual_flow_response(
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
    if not slug or get_dataset_or_none(slug) is None:
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
