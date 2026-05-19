# -*- coding: utf-8 -*-
"""Helper ``with_write_session`` — write-path equivalent of ``read_session.with_read_session``."""
from __future__ import annotations

from typing import Any, Callable, Literal, TypeVar

from sqlalchemy.exc import SQLAlchemyError

from infrastructure.db import is_engine_initialized
from infrastructure.db import write_session as _write_session

T = TypeVar("T")


def with_write_session(
    fn: Callable,
    default: T,
    *,
    session: Any = None,
    on_error: Literal["raise", "default"] = "default",
) -> T:
    """Run fn(sess) inside write_session, guarded by engine check.

    on_error='raise'  : re-raise SQLAlchemyError (insert/upsert).
    on_error='default': swallow error and return *default* (delete/update).
    """
    if session is None and not is_engine_initialized():
        if on_error == "raise":
            raise RuntimeError("Database engine not initialized")
        return default
    try:
        with _write_session(session) as sess:
            return fn(sess)
    except SQLAlchemyError:
        if on_error == "raise":
            raise
        return default
