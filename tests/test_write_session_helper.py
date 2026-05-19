# -*- coding: utf-8 -*-
"""Tests for models.write_session.with_write_session helper."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError


def test_with_write_session_returns_default_when_engine_not_initialized():
    from models.write_session import with_write_session
    called = []
    def fn(sess):
        called.append(True)
        return 99
    with patch("models.write_session.is_engine_initialized", return_value=False):
        result = with_write_session(fn, default=False)
    assert result is False
    assert called == []


def test_with_write_session_returns_result_when_callable_succeeds():
    from models.write_session import with_write_session
    from unittest.mock import MagicMock
    from contextlib import contextmanager
    mock_sess = MagicMock()
    @contextmanager
    def fake_write_session(session):
        yield mock_sess
    with (
        patch("models.write_session.is_engine_initialized", return_value=True),
        patch("models.write_session._write_session", fake_write_session),
    ):
        result = with_write_session(lambda sess: 99, default=0)
    assert result == 99


def test_with_write_session_reraises_when_on_error_is_raise():
    from models.write_session import with_write_session
    from unittest.mock import MagicMock
    from contextlib import contextmanager
    mock_sess = MagicMock()
    @contextmanager
    def fake_write_session(session):
        yield mock_sess
    def fn(sess):
        raise SQLAlchemyError("boom")
    with (
        patch("models.write_session.is_engine_initialized", return_value=True),
        patch("models.write_session._write_session", fake_write_session),
    ):
        with pytest.raises(SQLAlchemyError):
            with_write_session(fn, default=False, on_error="raise")


def test_with_write_session_returns_default_when_on_error_is_default():
    from models.write_session import with_write_session
    from unittest.mock import MagicMock
    from contextlib import contextmanager
    mock_sess = MagicMock()
    @contextmanager
    def fake_write_session(session):
        yield mock_sess
    def fn(sess):
        raise SQLAlchemyError("boom")
    with (
        patch("models.write_session.is_engine_initialized", return_value=True),
        patch("models.write_session._write_session", fake_write_session),
    ):
        result = with_write_session(fn, default=False, on_error="default")
    assert result is False
