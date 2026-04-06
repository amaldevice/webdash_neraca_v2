# -*- coding: utf-8 -*-
"""Regression: application factory produces isolated apps with routes registered."""
from __future__ import annotations

import importlib

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
    assert "data_management" in names
    assert "aggregated_summary" in names


def test_module_level_app_is_flask_instance(db_path, monkeypatch):
    from flask import Flask

    monkeypatch.setattr(models, "DB_PATH", str(db_path))
    models.init_db()
    import app as app_module

    importlib.reload(app_module)
    assert isinstance(app_module.app, Flask)
    assert "landing_page" in {r.endpoint for r in app_module.app.url_map.iter_rules() if r.endpoint}
