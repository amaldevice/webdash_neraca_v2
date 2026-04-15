"""DATABASE_URL helpers (GitHub issue #9 / SQLAlchemy migration P1)."""

from __future__ import annotations

from importlib import reload

import pytest


def test_database_url_defaults_when_env_unset(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import models

    db_file = tmp_path / "cfg.db"
    monkeypatch.setattr(models, "DB_PATH", str(db_file))
    import config

    reload(config)
    url = config.database_url()
    assert url.startswith("sqlite:///")
    assert str(db_file.resolve()).replace("\\", "/") in url.replace("\\", "/")
    assert config.use_sqlalchemy() is True
    assert config.database_url_explicit() is None


def test_database_url_explicit_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    import config

    reload(config)
    assert config.database_url() == "sqlite:///:memory:"
    assert config.database_url_explicit() == "sqlite:///:memory:"
    assert config.use_sqlalchemy() is True
