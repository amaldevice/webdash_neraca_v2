# -*- coding: utf-8 -*-
"""Tests for cache_upload_preview as a pure function (no Flask context required)."""
from __future__ import annotations

from services.upload_preview import cache_upload_preview, load_preview_session


def _payload():
    return {"layout": "vertical", "header_row": 1, "source_rows": [], "source_columns": [],
            "source_mode": "headered", "entries": [], "sample": [], "warnings": [], "invalid_rows": []}


def _meta():
    return {"uploader": "U1", "version": "v1", "data_type": "flow", "time_period": "monthly"}


def test_cache_upload_preview_returns_token_without_app_context(tmp_path):
    d = tmp_path / "preview"; d.mkdir()
    f = d / "sample.xlsx"; f.write_bytes(b"x")
    token = cache_upload_preview(str(d), str(f), "sample.xlsx", _meta(), _payload(), [], old_token=None)
    assert isinstance(token, str) and len(token) == 32


def test_cache_upload_preview_invalidates_old_token(tmp_path):
    d = tmp_path / "preview"; d.mkdir()
    f1 = d / "old.xlsx"; f1.write_bytes(b"old")
    f2 = d / "new.xlsx"; f2.write_bytes(b"new")
    old = cache_upload_preview(str(d), str(f1), "old.xlsx", _meta(), _payload(), [], old_token=None)
    assert load_preview_session(str(d), old) is not None
    new = cache_upload_preview(str(d), str(f2), "new.xlsx", _meta(), _payload(), [], old_token=old)
    assert new != old
    assert load_preview_session(str(d), old) is None
    assert load_preview_session(str(d), new) is not None
