# -*- coding: utf-8 -*-
"""Cross-dialect duplicate / unique-key detection for upload and persistence layers."""
from __future__ import annotations

import sqlite3
from typing import Any

from sqlalchemy.exc import IntegrityError as SAIntegrityError


def resolve_duplicate_check_dialect() -> str:
    """Dialect label for ``is_duplicate_key_error`` — SA engine when active, else ``sqlite`` (raw ``sqlite3``)."""
    try:
        from infrastructure.db import engine_dialect_name

        return engine_dialect_name() or "sqlite"
    except Exception:
        return "sqlite"


def _sqlite_duplicate_from_message(msg: str) -> bool:
    m = msg.lower()
    if "unique constraint failed" in m:
        return True
    if "unique constraint" in m and "violates" in m:
        return True
    if "duplicate key" in m:
        return True
    if "duplicate entry" in m:
        return True
    return False


def _mysql_duplicate_from_orig(orig: BaseException | None) -> bool:
    if orig is None:
        return False
    args: Any = getattr(orig, "args", ())
    if args and isinstance(args[0], int) and args[0] == 1062:
        return True
    s = str(orig).lower()
    return "duplicate entry" in s or "1062" in s


def _postgresql_duplicate_from_orig(orig: BaseException | None) -> bool:
    if orig is None:
        return False
    if getattr(orig, "pgcode", None) == "23505":
        return True
    return "uniqueviolation" in type(orig).__name__.lower()


def is_duplicate_key_error(exc: BaseException, dialect_name: str) -> bool:
    """
    True when ``exc`` represents a duplicate key / unique violation (not generic FK/NOT NULL noise).

    ``dialect_name``: ``sqlite`` | ``mysql`` | ``postgresql`` (from ``resolve_duplicate_check_dialect()``).
    """
    if isinstance(exc, sqlite3.IntegrityError):
        return _sqlite_duplicate_from_message(str(exc))

    if isinstance(exc, SAIntegrityError):
        orig = exc.orig
        if dialect_name == "mysql":
            return _mysql_duplicate_from_orig(orig) or _mysql_duplicate_from_orig(exc)
        if dialect_name == "postgresql":
            return _postgresql_duplicate_from_orig(orig) or _postgresql_duplicate_from_orig(exc)
        if dialect_name == "sqlite":
            if isinstance(orig, sqlite3.IntegrityError):
                return _sqlite_duplicate_from_message(str(orig))
            return _sqlite_duplicate_from_message(str(exc))

        # Unknown SA dialect: try portable heuristics
        if isinstance(orig, sqlite3.IntegrityError):
            return _sqlite_duplicate_from_message(str(orig))
        if _postgresql_duplicate_from_orig(orig):
            return True
        if _mysql_duplicate_from_orig(orig):
            return True
        return _sqlite_duplicate_from_message(str(exc))

    return False
