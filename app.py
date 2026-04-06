# -*- coding: utf-8 -*-
"""Flask application factory and module-level ``app`` for WSGI/tests."""
from __future__ import annotations

import os

from flask import Flask

from config import configure_flask_app
from models import init_db
from periods import parse_period_date
from routes import register_routes
from services.manual_entries import build_manual_entry
from services.validation import allowed_file, validate_metadata


def create_app(*, testing: bool = False) -> Flask:
    application = Flask(__name__)
    configure_flask_app(application, testing=bool(testing))
    application.config["TESTING"] = bool(testing)
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
