# -*- coding: utf-8 -*-
"""Unit tests for models/read_session.py helper."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from models.read_session import with_read_session


def test_read_session_returns_default_when_callable_raises():
    """Callable raises SQLAlchemyError → helper returns default."""
    mock_sess = MagicMock()

    def bad_fn(sess):
        raise SQLAlchemyError("db error")

    with patch("models.read_session.is_engine_initialized", return_value=True), \
         patch("models.read_session.get_session", return_value=mock_sess):
        result = with_read_session(bad_fn, default=-1)

    assert result == -1


def test_read_session_returns_callable_result_when_session_works():
    """Callable returns 42 → helper returns 42."""
    mock_sess = MagicMock()

    def good_fn(sess):
        return 42

    with patch("models.read_session.is_engine_initialized", return_value=True), \
         patch("models.read_session.get_session", return_value=mock_sess):
        result = with_read_session(good_fn, default=-1)

    assert result == 42


def test_read_session_returns_default_when_engine_not_initialized():
    """is_engine_initialized() False, session=None → default returned, callable never called."""
    called = []

    def should_not_be_called(sess):
        called.append(True)
        return 99

    with patch("models.read_session.is_engine_initialized", return_value=False):
        result = with_read_session(should_not_be_called, default="fallback")

    assert result == "fallback"
    assert called == [], "callable should not have been invoked"
