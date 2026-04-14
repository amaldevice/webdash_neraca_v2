# -*- coding: utf-8 -*-
"""Flask application factory and module-level ``app`` for WSGI/tests."""
from __future__ import annotations

import logging
import os
import uuid
from time import perf_counter

from flask import Flask, g, request

from config import configure_flask_app
from models import init_db
from periods import parse_period_date
from routes import register_routes
from services.manual_entries import build_manual_entry
from services.validation import allowed_file, validate_metadata

_request_log = logging.getLogger(__name__)


def create_app(*, testing: bool = False) -> Flask:
    application = Flask(__name__)
    configure_flask_app(application, testing=bool(testing))
    application.config["TESTING"] = bool(testing)

    @application.before_request
    def _assign_request_context() -> None:
        g.request_id = str(uuid.uuid4())
        g._request_t0 = perf_counter()

    @application.after_request
    def _request_id_and_access_log(response):
        rid = getattr(g, "request_id", None)
        if rid:
            response.headers["X-Request-ID"] = rid
        t0 = getattr(g, "_request_t0", None)
        duration_ms = None
        if t0 is not None:
            duration_ms = round((perf_counter() - t0) * 1000.0, 2)
        _request_log.info(
            "request_complete path=%s method=%s status=%s duration_ms=%s request_id=%s",
            request.path,
            request.method,
            response.status_code,
            duration_ms,
            getattr(g, "request_id", ""),
        )
        return response

    register_routes(application)
    init_db()
    return application


app = create_app()

# Test / legacy aliases (see tests/test_bugs.py)
_parse_period_date = parse_period_date
_build_manual_entry = build_manual_entry

__all__ = [
    "app",
    "create_app",
    "_build_manual_entry",
    "_parse_period_date",
    "allowed_file",
    "validate_metadata",
]


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("FLASK_RUN_PORT", 5000)))
