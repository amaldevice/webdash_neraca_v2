"""DATABASE_URL helpers (GitHub issue #9 / SQLAlchemy migration P1)."""

from __future__ import annotations

import pytest


def test_database_url_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from config import database_url, use_sqlalchemy

    assert database_url() is None
    assert use_sqlalchemy() is False


def test_database_url_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    from importlib import reload

    import config

    reload(config)
    assert config.database_url() == "sqlite:///:memory:"
    assert config.use_sqlalchemy() is True
