# -*- coding: utf-8 -*-
"""Application configuration: paths, upload limits, and validation sets."""
from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

ALLOWED_EXTENSIONS = {"xls", "xlsx"}
ALLOWED_DATA_TYPES = {"flow", "stock"}
ALLOWED_TIME_PERIODS = {"monthly", "quarterly", "yearly"}

UPLOAD_PREVIEW_TTL_SECONDS = 20 * 60
MAX_UPLOAD_BYTES = 16 * 1024 * 1024
DEFAULT_SECRET_KEY = "change-me-for-production"


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
    app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    key = resolve_secret_key()
    app.config["SECRET_KEY"] = key

    if key == DEFAULT_SECRET_KEY and _env_truthy("REQUIRE_FLASK_SECRET"):
        raise RuntimeError(
            "REQUIRE_FLASK_SECRET is set but FLASK_SECRET_KEY is missing or still default. "
            "Set a strong FLASK_SECRET_KEY in the environment."
        )

    if default_secret_risk_in_production(testing=testing, secret_key=key) and "pytest" not in sys.modules:
        logger.warning(
            "SECRET_KEY is still the default; set FLASK_SECRET_KEY in production."
        )
