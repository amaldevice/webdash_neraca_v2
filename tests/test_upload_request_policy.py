# -*- coding: utf-8 -*-
from __future__ import annotations

from unittest.mock import patch

import pytest

from routes import upload_request_policy as policy


@pytest.fixture(autouse=True)
def _clear_rate_limit_buckets():
    with policy._RATE_LIMIT_LOCK:
        policy._RATE_LIMIT_STATE.clear()
    yield
    with policy._RATE_LIMIT_LOCK:
        policy._RATE_LIMIT_STATE.clear()


def test_evaluate_upload_csrf_rejects_mismatch(app_module):
    app = app_module.app
    with app.test_request_context("/upload", method="POST", data={"csrf_token": "wrong"}):
        from flask import session

        session["_upload_csrf_token"] = "good"
        assert not policy.evaluate_upload_csrf().allowed


def test_evaluate_upload_rate_limit_blocks_when_bucket_full(app_module):
    app = app_module.app
    app.config["UPLOAD_RATE_LIMIT_MAX_REQUESTS"] = 2
    app.config["UPLOAD_RATE_LIMIT_WINDOW_SECONDS"] = 60
    t0 = 1000.0
    times = iter([t0, t0 + 0.01, t0 + 0.02])

    def fake_mono():
        return next(times)

    with patch.object(policy.time, "monotonic", side_effect=fake_mono):
        with patch.object(policy, "upload_client_key", return_value="fixed-client"):
            with app.test_request_context("/upload", method="POST"):
                assert policy.evaluate_upload_rate_limit().allowed
            with app.test_request_context("/upload", method="POST"):
                assert policy.evaluate_upload_rate_limit().allowed
            with app.test_request_context("/upload", method="POST"):
                d = policy.evaluate_upload_rate_limit()
                assert not d.allowed
