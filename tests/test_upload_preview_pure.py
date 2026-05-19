# -*- coding: utf-8 -*-
"""Pure (no-Flask-context) tests for cache_upload_preview after issue-#102 refactor."""
from __future__ import annotations

import pytest

from services.upload_preview import cache_upload_preview, load_preview_session


def _entry_payload() -> dict:
    return {
        "uploader": "U1",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
    }


def _parse_payload() -> dict:
    return {
        "layout": "vertical",
        "header_row": 1,
        "source_rows": [],
        "source_columns": [],
        "source_mode": "headered",
        "entries": [
            {
                "indicator_name": "GDP",
                "value": 1.0,
                "unit": None,
                "region_code": None,
                "year": 2024,
                "month": 3,
                "quarter": None,
            }
        ],
        "sample": [],
        "warnings": [],
        "invalid_rows": [],
    }


def test_cache_upload_preview_returns_token_without_app_context(tmp_path):
    """cache_upload_preview tidak boleh butuh Flask app context (tidak akses session)."""
    upload_dir = tmp_path / "preview"
    upload_dir.mkdir()
    file_path = upload_dir / "sample.xlsx"
    file_path.write_bytes(b"x")

    # Dipanggil tanpa app context sama sekali — tidak boleh raise RuntimeError
    token = cache_upload_preview(
        str(upload_dir),
        str(file_path),
        "sample.xlsx",
        _entry_payload(),
        _parse_payload(),
        [],
        old_token=None,
    )
    assert isinstance(token, str)
    assert len(token) == 32  # uuid4().hex


def test_cache_upload_preview_invalidates_old_token(tmp_path):
    """Jika old_token diberikan, session lama di-invalidate."""
    upload_dir = tmp_path / "preview"
    upload_dir.mkdir()

    file_path_old = upload_dir / "old.xlsx"
    file_path_old.write_bytes(b"old")
    file_path_new = upload_dir / "new.xlsx"
    file_path_new.write_bytes(b"new")

    # Buat session lama dulu
    old_token = cache_upload_preview(
        str(upload_dir),
        str(file_path_old),
        "old.xlsx",
        _entry_payload(),
        _parse_payload(),
        [],
        old_token=None,
    )

    # Pastikan session lama ada
    assert load_preview_session(str(upload_dir), old_token) is not None

    # Buat session baru, teruskan old_token
    new_token = cache_upload_preview(
        str(upload_dir),
        str(file_path_new),
        "new.xlsx",
        _entry_payload(),
        _parse_payload(),
        [],
        old_token=old_token,
    )

    assert new_token != old_token
    # Session lama harus sudah di-invalidate
    assert load_preview_session(str(upload_dir), old_token) is None
    # Session baru harus ada
    assert load_preview_session(str(upload_dir), new_token) is not None
