# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from flask import Flask

from config import DEFAULT_SECRET_KEY, configure_flask_app, default_secret_risk_in_production

ROOT = Path(__file__).resolve().parents[1]


def test_require_flask_secret_raises_when_default_key(monkeypatch):
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.setenv("REQUIRE_FLASK_SECRET", "1")
    app = Flask(__name__)
    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        configure_flask_app(app, testing=False)


def test_default_secret_risk_predicate(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    assert default_secret_risk_in_production(testing=False, secret_key=DEFAULT_SECRET_KEY)
    assert not default_secret_risk_in_production(testing=True, secret_key=DEFAULT_SECRET_KEY)
    assert not default_secret_risk_in_production(
        testing=False, secret_key="custom-secret-not-default"
    )
    monkeypatch.delenv("FLASK_ENV", raising=False)
    assert not default_secret_risk_in_production(testing=False, secret_key=DEFAULT_SECRET_KEY)


def test_subprocess_production_config_logs_secret_warning():
    """Without pytest in sys.modules, configure_flask_app should emit the warning."""
    env = os.environ.copy()
    env.pop("FLASK_SECRET_KEY", None)
    env["FLASK_ENV"] = "production"
    env["PYTHONPATH"] = str(ROOT)
    env.pop("REQUIRE_FLASK_SECRET", None)
    code = textwrap.dedent(
        """
        import logging
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
        from flask import Flask
        from config import configure_flask_app
        configure_flask_app(Flask(__name__), testing=False)
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    out = proc.stdout + proc.stderr
    assert "FLASK_SECRET_KEY" in out, out


def test_testing_mode_skips_production_secret_warning(monkeypatch, caplog):
    import logging

    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")
    app = Flask(__name__)
    with caplog.at_level(logging.WARNING, logger="config"):
        configure_flask_app(app, testing=True)
    assert not [r for r in caplog.records if "SECRET_KEY" in r.getMessage()]


def test_custom_secret_no_warning_in_production(monkeypatch, caplog):
    import logging

    monkeypatch.setenv("FLASK_SECRET_KEY", "not-the-default-secret-value")
    monkeypatch.setenv("FLASK_ENV", "production")
    app = Flask(__name__)
    with caplog.at_level(logging.WARNING, logger="config"):
        configure_flask_app(app, testing=False)
    assert not [r for r in caplog.records if "SECRET_KEY" in r.getMessage()]
