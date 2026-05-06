# -*- coding: utf-8 -*-
"""Regression: default pytest process keeps a SQLite file DSN (see tests/conftest.py)."""
from __future__ import annotations

import os

import pytest


def _uses_env_database_url() -> bool:
    return os.environ.get("USE_ENV_DATABASE_URL_FOR_TESTS", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


@pytest.mark.skipif(_uses_env_database_url(), reason="remote dialect smoke opts into env DATABASE_URL")
def test_default_suite_database_url_is_sqlite() -> None:
    """Without USE_ENV_DATABASE_URL_FOR_TESTS, root conftest forces in-repo SQLite before models load."""
    url = os.environ.get("DATABASE_URL", "").strip()
    assert url.startswith("sqlite:"), f"expected sqlite DSN for default suite, got {url!r}"
