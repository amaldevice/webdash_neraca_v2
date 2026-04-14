# -*- coding: utf-8 -*-
"""Request correlation: X-Request-ID header and g.request_id within a request."""
from __future__ import annotations

import importlib

import models


def test_request_id_header_on_landing(client):
    resp = client.get("/")
    assert resp.status_code == 200
    rid = resp.headers.get("X-Request-ID")
    assert rid
    assert len(rid) >= 8


def test_request_id_available_on_g_within_request(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    import app as app_module

    importlib.reload(app_module)
    application = app_module.create_app(testing=True)
    seen: dict[str, str | None] = {}

    @application.before_request
    def _capture_rid():
        from flask import g

        seen["rid"] = getattr(g, "request_id", None)

    with application.test_client() as c:
        c.get("/")
    assert seen.get("rid")
