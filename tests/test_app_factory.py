# -*- coding: utf-8 -*-
"""Regression: application factory produces isolated apps with routes registered."""
from __future__ import annotations

import importlib

import pytest

import models


def test_create_app_returns_new_instance_each_call(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    import app as app_module

    importlib.reload(app_module)
    a = app_module.create_app(testing=True)
    b = app_module.create_app(testing=True)
    assert a is not b
    assert a.testing is True
    assert b.testing is True


def test_create_app_registers_core_endpoints(db_path, monkeypatch):
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    import app as app_module

    importlib.reload(app_module)
    application = app_module.create_app(testing=True)
    names = {r.endpoint for r in application.url_map.iter_rules() if r.endpoint is not None}
    assert "landing_page" in names
    assert "upload_data" in names
    assert "upload_dataset_template" in names
    assert "data_management" in names


def test_module_level_app_is_flask_instance(db_path, monkeypatch):
    from flask import Flask

    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    import app as app_module

    importlib.reload(app_module)
    assert isinstance(app_module.app, Flask)
    assert "landing_page" in {r.endpoint for r in app_module.app.url_map.iter_rules() if r.endpoint}


def test_create_app_requires_database_url_in_production(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import app as app_module

    importlib.reload(app_module)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        app_module.create_app(testing=False, init_sqlalchemy=False)


def test_create_app_sqlalchemy_engine_when_database_url_set(db_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    from infrastructure.db import dispose_engine, init_engine

    dispose_engine()
    init_engine("sqlite:///:memory:")
    models.init_db()
    import app as app_module

    importlib.reload(app_module)
    application = app_module.create_app(testing=True)
    from infrastructure.db import dispose_engine as dispose2, get_session

    try:
        with application.app_context():
            session = get_session()
            assert session.bind is not None
    finally:
        dispose2()
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from pathlib import Path

        from infrastructure.db import dispose_engine, init_engine

        p = Path(__file__).resolve().parents[1] / ".pytest_runtime_default.sqlite3"
        url = f"sqlite:///{p.resolve().as_posix()}"
        monkeypatch.setenv("DATABASE_URL", url)
        models.DB_PATH = str(p)
        dispose_engine()
        init_engine(url)
        models.init_db()
        importlib.reload(app_module)
