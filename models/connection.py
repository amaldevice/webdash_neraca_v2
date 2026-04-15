# -*- coding: utf-8 -*-
import os
import sqlite3
from contextlib import closing

from config import BASE_DIR, use_sqlalchemy

DB_PATH = os.path.join(BASE_DIR, "data.db")


def get_conn() -> sqlite3.Connection:
    # Resolve via package so tests can monkeypatch `models.DB_PATH` (same as monolithic models.py).
    import models as _models_pkg

    path = str(_models_pkg.DB_PATH)
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create legacy SQLite tables when not using an initialized SQLAlchemy engine (Alembic owns schema then)."""
    try:
        from infrastructure.db import is_engine_initialized

        if use_sqlalchemy() and is_engine_initialized():
            return
    except Exception:
        pass

    with closing(get_conn()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader_name TEXT NOT NULL,
                version TEXT NOT NULL,
                template_type TEXT,
                data_type TEXT,
                time_period TEXT,
                indicator_name TEXT NOT NULL,
                value REAL,
                unit TEXT,
                region_code TEXT,
                year INTEGER,
                month INTEGER,
                quarter INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_data_entry_variant
            ON data_entries(uploader_name, version, indicator_name, year, month, quarter);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS aggregated_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
