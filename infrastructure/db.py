# -*- coding: utf-8 -*-
"""SQLAlchemy engine + scoped session (P2 migration; used when DATABASE_URL is set)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

_engine: Engine | None = None
_scoped_factory: scoped_session[Session] | None = None


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite:"):
        if ":memory:" in url:
            return {
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False, "timeout": 30},
            }
        return {
            "poolclass": NullPool,
            # ``check_same_thread=False`` allows Flask test threads to share the file DB.
            "connect_args": {"timeout": 30, "check_same_thread": False},
        }
    return {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 2,
        "pool_recycle": 280,
    }


def init_engine(url: str) -> None:
    """Create (or replace) global engine and scoped_session factory."""
    global _engine, _scoped_factory
    dispose_engine()
    _engine = create_engine(url, **_engine_kwargs(url))
    _scoped_factory = scoped_session(
        sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    )


def is_engine_initialized() -> bool:
    """True after ``init_engine``; used to pick SQLAlchemy read path in ``models.queries``."""
    return _engine is not None


def get_engine() -> Engine | None:
    """Global engine after ``init_engine`` (read-only for schema helpers)."""
    return _engine


def engine_dialect_name() -> str | None:
    """``engine.dialect.name`` when engine exists (``sqlite`` | ``mysql`` | ``postgresql`` | …)."""
    if _engine is None:
        return None
    return _engine.dialect.name


def dispose_engine() -> None:
    """Release pool and drop references (tests / process re-init)."""
    global _engine, _scoped_factory
    if _scoped_factory is not None:
        _scoped_factory.remove()
        _scoped_factory = None
    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_session() -> Session:
    if _scoped_factory is None:
        raise RuntimeError("SQLAlchemy session not configured; set DATABASE_URL and call init_engine().")
    return _scoped_factory()


@contextmanager
def scoped_transaction() -> Generator[Session, None, None]:
    """One commit/rollback per write block (mutations, summary cache)."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise


@contextmanager
def write_session(session: Session | None) -> Generator[Session, None, None]:
    """
    Mutations: use global scoped transaction when session is None; otherwise use the
    provided Session (commit/rollback on this block only). For tests or nested tooling.
    """
    if session is not None:
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
    else:
        with scoped_transaction() as sess:
            yield sess


def remove_scoped_session() -> None:
    if _scoped_factory is not None:
        _scoped_factory.remove()


def register_flask_teardown(app: Flask) -> None:
    """Remove thread-local session after each app context (request)."""

    @app.teardown_appcontext
    def _teardown_sqlalchemy_session(exc: BaseException | None) -> None:  # noqa: ARG001
        remove_scoped_session()
