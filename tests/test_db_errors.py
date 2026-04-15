# -*- coding: utf-8 -*-
"""Unit tests for duplicate-key detection across DB dialects."""
from __future__ import annotations

import sqlite3

from sqlalchemy.exc import IntegrityError as SAIntegrityError

from services.db_errors import is_duplicate_key_error


def _sa_integrity(orig: BaseException | None) -> SAIntegrityError:
    return SAIntegrityError("stmt", {}, orig=orig)


def test_sqlite3_unique_message_true() -> None:
    exc = sqlite3.IntegrityError("UNIQUE constraint failed: entries.idx")
    assert is_duplicate_key_error(exc, "sqlite") is True


def test_sqlite3_fk_message_false() -> None:
    exc = sqlite3.IntegrityError("FOREIGN KEY constraint failed")
    assert is_duplicate_key_error(exc, "sqlite") is False


def test_sa_sqlite_dialect_uses_orig_sqlite3() -> None:
    orig = sqlite3.IntegrityError("UNIQUE constraint failed: x")
    assert is_duplicate_key_error(_sa_integrity(orig), "sqlite") is True


def test_sa_mysql_errno_1062() -> None:
    orig = Exception(1062, "Duplicate entry 'k' for key 'PRIMARY'")
    assert is_duplicate_key_error(_sa_integrity(orig), "mysql") is True


def test_sa_mysql_non_duplicate_errno() -> None:
    orig = Exception(1452, "Cannot add or update a child row")
    assert is_duplicate_key_error(_sa_integrity(orig), "mysql") is False


def test_sa_postgresql_pgcode_23505() -> None:
    class UniqueViolation(Exception):
        pgcode = "23505"

    orig = UniqueViolation("duplicate key value violates unique constraint")
    assert is_duplicate_key_error(_sa_integrity(orig), "postgresql") is True


def test_unknown_dialect_falls_back_to_orig_heuristics() -> None:
    class UniqueViolation(Exception):
        pgcode = "23505"

    assert is_duplicate_key_error(_sa_integrity(UniqueViolation("x")), "mssql") is True


def test_unknown_dialect_mysql_string_in_orig() -> None:
    orig = Exception("(1062, \"Duplicate entry 'a' for key 'uk'\")")
    assert is_duplicate_key_error(_sa_integrity(orig), "oracle") is True
