# -*- coding: utf-8 -*-
"""Flask application factory and module-level ``app`` for WSGI/tests."""
from __future__ import annotations

import os
import sys

from flask import Flask

from config import configure_flask_app, database_url
from infrastructure.db import dispose_engine, init_engine, register_flask_teardown
from models import init_db
from periods import parse_period_date
from routes import register_routes
from services.manual_entries import build_manual_entry
from services.validation import allowed_file, validate_metadata


def create_app(*, testing: bool = False, init_sqlalchemy: bool | None = None) -> Flask:
    """``init_sqlalchemy``: default False under pytest so ``models.DB_PATH`` + ``get_conn()`` stay aligned
    unless a test passes ``init_sqlalchemy=True`` (see ``tests/test_app_factory.py``).
    """
    application = Flask(__name__)
    configure_flask_app(application, testing=bool(testing))
    application.config["TESTING"] = bool(testing)
    register_routes(application)
    url = database_url()
    if (
        not testing
        and os.environ.get("FLASK_ENV", "").strip().lower() == "production"
        and not url
    ):
        raise RuntimeError(
            "Production requires DATABASE_URL (SQLAlchemy). "
            "Apply schema with `alembic upgrade head` on the target database before start."
        )
    if init_sqlalchemy is None:
        init_sqlalchemy = "pytest" not in sys.modules
    if url and init_sqlalchemy:
        init_engine(url)
        register_flask_teardown(application)
    else:
        dispose_engine()
    init_db()
    return application


app = create_app(testing="pytest" in sys.modules)

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
