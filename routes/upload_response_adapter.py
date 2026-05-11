# -*- coding: utf-8 -*-
"""Map upload/manual flow dataclasses to Flask responses (flash, session, redirect, templates)."""
from __future__ import annotations

import secrets

from flask import Response, current_app, flash, make_response, redirect, render_template, session, url_for

from services.dataset_catalog import datasets_for_template_context
from services.upload_flow import MANUAL_ROUTE_MODE, UPLOAD_ROUTE_MODE, UPLOAD_TEMPLATE_NAME
from services.upload_types import ManualFlowResponse, UploadFlowResponse
from services.timeutil import wita_now_iso


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


def _ensure_upload_version(form_values: dict | None) -> dict[str, str]:
    values = dict(form_values or {})
    values.setdefault("version", wita_now_iso())
    values.setdefault("dataset_slug", "")
    return values


def _render_upload_template(
    *,
    preview: dict | None,
    upload_preview_token: str | None,
    form_values: dict | None = None,
) -> Response:
    form_values = _ensure_upload_version(form_values)
    form_values["dataset_slug"] = "universal"
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


def apply_upload_flow_response(resp: UploadFlowResponse) -> Response:
    """Apply flashes/session side effects; return redirect or rendered upload page."""
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


def apply_manual_flow_response(resp: ManualFlowResponse):
    """Apply flashes; return redirect or rendered manual/upload template."""
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


__all__ = [
    "apply_manual_flow_response",
    "apply_upload_flow_response",
    "_dataset_wizard_template_kwargs",
    "_ensure_upload_version",
    "_render_upload_template",
]
