# -*- coding: utf-8 -*-
"""Application configuration: paths, upload limits, and validation sets."""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


class _JsonLogFormatter(logging.Formatter):
    """One JSON object per line (use LOG_FORMAT=json)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        if record.exc_info and record.exc_text:
            payload["exc_info"] = record.exc_text
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(app: "Flask", *, testing: bool = False) -> None:
    """Root + app logger level/format from env (idempotent if handlers already exist)."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt_env = os.environ.get(
        "LOG_FORMAT",
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if not logging.root.handlers:
        if fmt_env.strip().lower() == "json":
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(_JsonLogFormatter())
            logging.root.addHandler(handler)
        else:
            logging.basicConfig(level=level, format=fmt_env, stream=sys.stderr)
    logging.root.setLevel(level)
    app.logger.setLevel(level)
    if testing:
        app.logger.debug("Logging configured (testing=True)")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

ALLOWED_EXTENSIONS = {"xls", "xlsx"}
ALLOWED_DATA_TYPES = {"flow", "stock"}
ALLOWED_TIME_PERIODS = {"monthly", "quarterly", "yearly"}

UPLOAD_PREVIEW_TTL_SECONDS = 20 * 60
MAX_UPLOAD_BYTES = 16 * 1024 * 1024
DEFAULT_SECRET_KEY = "change-me-for-production"
DEFAULT_UPLOAD_RATE_LIMIT_PER_MINUTE = 120
DEFAULT_UPLOAD_RATE_LIMIT_WINDOW_SECONDS = 60


def resolve_secret_key() -> str:
    return os.environ.get("FLASK_SECRET_KEY", DEFAULT_SECRET_KEY)


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def default_secret_risk_in_production(*, testing: bool, secret_key: str) -> bool:
    """True when FLASK_ENV=production and the app still uses the built-in default secret."""
    if testing or secret_key != DEFAULT_SECRET_KEY:
        return False
    return os.environ.get("FLASK_ENV", "").strip().lower() == "production"


def configure_flask_app(app: Flask, *, testing: bool = False) -> None:
    """Apply standard Flask config (upload folder, body limit, secret key)."""
    configure_logging(app, testing=testing)
    app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    key = resolve_secret_key()
    app.config["SECRET_KEY"] = key
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = _env_truthy("SESSION_COOKIE_SECURE")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["UPLOAD_RATE_LIMIT_MAX_REQUESTS"] = int(
        os.environ.get("UPLOAD_RATE_LIMIT_MAX_REQUESTS", str(DEFAULT_UPLOAD_RATE_LIMIT_PER_MINUTE))
    )
    app.config["UPLOAD_RATE_LIMIT_WINDOW_SECONDS"] = int(
        os.environ.get("UPLOAD_RATE_LIMIT_WINDOW_SECONDS", str(DEFAULT_UPLOAD_RATE_LIMIT_WINDOW_SECONDS))
    )

    if key == DEFAULT_SECRET_KEY and _env_truthy("REQUIRE_FLASK_SECRET"):
        raise RuntimeError(
            "REQUIRE_FLASK_SECRET is set but FLASK_SECRET_KEY is missing or still default. "
            "Set a strong FLASK_SECRET_KEY in the environment."
        )

    if default_secret_risk_in_production(testing=testing, secret_key=key) and "pytest" not in sys.modules:
        logger.warning(
            "SECRET_KEY is still the default; set FLASK_SECRET_KEY in production."
        )
