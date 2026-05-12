# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import get_flashed_messages

from routes.upload_response_adapter import apply_upload_flow_response
from services.upload_types import build_upload_response


def test_apply_upload_flow_response_redirect_pops_preview_token(app_module):
    app = app_module.app
    with app.test_request_context():
        from flask import session

        session["upload_preview_token"] = "tok"
        resp = apply_upload_flow_response(
            build_upload_response(
                "redirect",
                [("done", "info")],
                pop_upload_session_token=True,
            )
        )
        assert resp.status_code == 302
        assert "upload_preview_token" not in session
        cats = get_flashed_messages(with_categories=True)
        assert cats == [("info", "done")]


def test_apply_upload_flow_response_render_sets_flashes(app_module, tmp_path):
    app = app_module.app
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    with app.test_request_context():
        resp = apply_upload_flow_response(
            build_upload_response(
                "render",
                [("x", "warning")],
                preview=None,
                upload_preview_token=None,
                form_values={
                    "uploader": "u",
                    "version": "v1",
                    "data_type": "flow",
                    "time_period": "monthly",
                    "dataset_slug": "universal",
                },
            )
        )
        assert resp.status_code == 200
        assert get_flashed_messages(with_categories=True) == [("warning", "x")]
