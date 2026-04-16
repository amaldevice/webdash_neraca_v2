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


def _load_dotenv_into_os_environ() -> None:
    """Load ``.env`` from project root (and optional ``DOTENV_PATH``) without overriding existing env.

    Production: prefer systemd / service manager ``Environment=`` — those win over file values.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)
    extra = os.environ.get("DOTENV_PATH", "").strip()
    if extra:
        load_dotenv(extra, override=False)


_load_dotenv_into_os_environ()


def database_url_explicit() -> str | None:
    """``DATABASE_URL`` from environment only (empty → ``None``). Used for production guard."""
    raw = os.environ.get("DATABASE_URL", "").strip()
    return raw or None


def database_url() -> str:
    """Effective SQLAlchemy DSN: ``DATABASE_URL`` or default ``sqlite:///`` file at ``models.DB_PATH``."""
    raw = os.environ.get("DATABASE_URL", "").strip()
    if raw:
        return raw
    from pathlib import Path

    try:
        import models as _m

        p = Path(str(_m.DB_PATH)).resolve()
    except Exception:
        p = (Path(BASE_DIR) / "data.db").resolve()
    return f"sqlite:///{p.as_posix()}"


def use_sqlalchemy() -> bool:
    """Always true: persistence goes through SQLAlchemy (including default SQLite file)."""
    return True


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


def require_dataset_for_upload() -> bool:
    """Jika True, unggah Excel wajib memilih `dataset_slug` (Fase 0–2 dataset-aware). Default: legacy boleh kosong."""
    return _env_truthy("REQUIRE_DATASET_FOR_UPLOAD")


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
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = _env_truthy("SESSION_COOKIE_SECURE")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["UPLOAD_RATE_LIMIT_MAX_REQUESTS"] = int(
        os.environ.get("UPLOAD_RATE_LIMIT_MAX_REQUESTS", str(DEFAULT_UPLOAD_RATE_LIMIT_PER_MINUTE))
    )
    app.config["UPLOAD_RATE_LIMIT_WINDOW_SECONDS"] = int(
        os.environ.get("UPLOAD_RATE_LIMIT_WINDOW_SECONDS", str(DEFAULT_UPLOAD_RATE_LIMIT_WINDOW_SECONDS))
    )
    app.config["REQUIRE_DATASET_FOR_UPLOAD"] = require_dataset_for_upload()

    if key == DEFAULT_SECRET_KEY and _env_truthy("REQUIRE_FLASK_SECRET"):
        raise RuntimeError(
            "REQUIRE_FLASK_SECRET is set but FLASK_SECRET_KEY is missing or still default. "
            "Set a strong FLASK_SECRET_KEY in the environment."
        )

    if default_secret_risk_in_production(testing=testing, secret_key=key) and "pytest" not in sys.modules:
        logger.warning(
            "SECRET_KEY is still the default; set FLASK_SECRET_KEY in production."
        )
