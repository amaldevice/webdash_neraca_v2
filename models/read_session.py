from __future__ import annotations

from typing import Any, Callable, TypeVar

from sqlalchemy.exc import SQLAlchemyError

from infrastructure.db import get_session, is_engine_initialized

T = TypeVar("T")


def with_read_session(fn: Callable, default: T, *, session: Any = None) -> T:
    """Run fn(session) guarded by engine check + SQLAlchemyError → default."""
    if session is None and not is_engine_initialized():
        return default
    try:
        sess = session if session is not None else get_session()
    except SQLAlchemyError:
        return default
    try:
        return fn(sess)
    except SQLAlchemyError:
        return default
