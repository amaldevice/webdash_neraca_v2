"""DATABASE_URL helpers (GitHub issue #9 / SQLAlchemy migration P1)."""

from __future__ import annotations

import os
from importlib import reload

import pytest


def test_database_url_defaults_when_env_unset(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import models

    db_file = tmp_path / "cfg.db"
    monkeypatch.setattr(models, "DB_PATH", str(db_file))

    # Remove DATABASE_URL and prevent .env from restoring it
    monkeypatch.delenv("DATABASE_URL", raising=False)
    original_get = os.environ.get

    def patched_get(key, *args, **kwargs):
        if key == "DATABASE_URL":
            return ""
        return original_get(key, *args, **kwargs)

    monkeypatch.setattr(os.environ, "get", patched_get)

    import config

    reload(config)
    url = config.database_url()
    assert url.startswith("sqlite:///"), f"Expected sqlite, got: {url}"
    assert str(db_file.resolve()).replace("\\", "/") in url.replace("\\", "/")
    assert config.database_url_explicit() is None


def test_database_url_explicit_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setattr("config._load_dotenv_into_os_environ", lambda: None)
    import config

    reload(config)
    assert config.database_url() == "sqlite:///:memory:"
    assert config.database_url_explicit() == "sqlite:///:memory:"
