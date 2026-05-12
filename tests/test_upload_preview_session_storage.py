# -*- coding: utf-8 -*-
from __future__ import annotations

from services.upload_preview_session_storage import file_backed_upload_preview_session_store


def test_file_backed_preview_session_store_roundtrip(tmp_path) -> None:
    root = str(tmp_path / "uploads")
    store = file_backed_upload_preview_session_store(root)
    payload = {
        "file_path": str(tmp_path / "f.xlsx"),
        "file_name": "f.xlsx",
        "metadata": {"uploader": "a", "version": "1", "data_type": "flow", "time_period": "monthly"},
    }
    store.save_session("tok1", payload)
    loaded = store.load_session("tok1")
    assert loaded is not None
    assert loaded.get("metadata", {}).get("uploader") == "a"
    store.delete_session("tok1")
    assert store.load_session("tok1") is None
