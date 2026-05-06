# -*- coding: utf-8 -*-
"""Flask application factory and module-level ``app`` for WSGI/tests."""
from __future__ import annotations

import os
import sys

from flask import Flask

from config import configure_flask_app, database_url, database_url_explicit
from infrastructure.db import dispose_engine, init_engine, register_flask_teardown
from models import init_db
from routes import register_routes
from services.timeutil import to_wita_iso
from services.validation import allowed_file, validate_metadata


def create_app(*, testing: bool = False, init_sqlalchemy: bool | None = None) -> Flask:
    """``init_sqlalchemy``: default ``True`` (SQLAlchemy + ``database_url()``). Pass ``False`` only in tests that assert startup without an engine."""
    application = Flask(__name__)
    configure_flask_app(application, testing=bool(testing))
    application.config["TESTING"] = bool(testing)
    register_routes(application)
    explicit = database_url_explicit()
    if (
        not testing
        and os.environ.get("FLASK_ENV", "").strip().lower() == "production"
        and not explicit
    ):
        raise RuntimeError(
            "Production requires DATABASE_URL (SQLAlchemy). "
            "Apply schema with `alembic upgrade head` on the target database before start."
        )
    if init_sqlalchemy is None:
        init_sqlalchemy = True
    url = database_url()
    if init_sqlalchemy:
        init_engine(url)
        register_flask_teardown(application)
    else:
        dispose_engine()
    init_db()
    application.jinja_env.filters["to_wita"] = to_wita_iso
    return application


app = create_app(testing="pytest" in sys.modules)

__all__ = [
    "app",
    "create_app",
    "allowed_file",
    "validate_metadata",
]


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("FLASK_RUN_PORT", 5000)))
