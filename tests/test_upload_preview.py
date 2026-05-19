import json
import os

import models
from services import upload_preview
from services.upload_preview import (
    build_upload_preview,
    cache_upload_preview,
    cleanup_upload_preview_cache,
    find_duplicate_entries_in_db,
    load_preview_session,
    save_preview_session,
    to_preview_context,
)


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
                "uploader_name": "U1",
                "version": "v1",
                "template_type": "excel",
                "data_type": "flow",
                "time_period": "monthly",
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


def test_cache_upload_preview_and_load_session(app_module, tmp_path):
    upload_dir = tmp_path / "preview"
    upload_dir.mkdir()
    file_path = upload_dir / "sample.xlsx"
    file_path.write_bytes(b"x")
    destination = str(file_path)

    with app_module.app.test_request_context():
        token = cache_upload_preview(
            str(upload_dir),
            destination,
            "sample.xlsx",
            _entry_payload(),
            _parse_payload(),
            [],
        )
        assert isinstance(token, str)
        # session is no longer written by cache_upload_preview (caller's responsibility)

        payload = load_preview_session(str(upload_dir), token)
        assert payload is not None
        assert payload["file_name"] == "sample.xlsx"
        assert payload["metadata"] == _entry_payload()
        assert payload["skip_duplicate_indexes"] == []


def test_build_upload_preview_returns_payload_and_token(app_module, tmp_path):
    upload_dir = tmp_path / "preview"
    upload_dir.mkdir()
    file_path = upload_dir / "preview.xlsx"
    file_path.write_bytes(b"x")

    duplicates = [
        {
            "indicator_name": "GDP",
            "year": 2024,
            "month": 3,
            "quarter": None,
            "dataset_code": "",
        }
    ]

    with app_module.app.test_request_context():
        token, preview = build_upload_preview(
            upload_folder=str(upload_dir),
            destination=str(file_path),
            display_name="preview.xlsx",
            uploader="U1",
            version="v1",
            data_type="flow",
            time_period="monthly",
            payload=_parse_payload(),
            entries=_parse_payload()["entries"],
            duplicates=duplicates,
        )
        # session is now managed by the route adapter, not by build_upload_preview
        assert preview["upload_preview_token"] == token
        assert preview["duplicate_records"] == duplicates
        assert preview["skip_duplicate_indexes"] == []


def test_load_preview_session_expired_session_is_removed(tmp_path):
    upload_dir = tmp_path / "preview"
    upload_dir.mkdir()
    file_path = upload_dir / "x.xlsx"
    file_path.write_bytes(b"x")
    token = "expired-token"
    payload = {
        "file_path": str(file_path),
        "file_name": "x.xlsx",
        "metadata": _entry_payload(),
        "layout": "vertical",
        "header_row": 1,
        "source_rows": [],
        "source_columns": [],
        "source_mode": "headered",
        "warnings": [],
        "entries_preview": [],
        "invalid_rows": [],
        "total_records": 0,
        "duplicate_records": [],
        "skip_duplicate_indexes": [],
    }
    save_preview_session(str(upload_dir), token, payload)
    session_file = upload_dir / "_preview_sessions" / token / "session.json"
    stale = {
        "created_at": 0,
        **payload,
    }
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(stale, f)

    session_data = load_preview_session(str(upload_dir), token)
    assert session_data is None
    assert not os.path.exists(upload_dir / "_preview_sessions" / token)


def test_cleanup_upload_preview_cache_removes_stale_token_from_session(tmp_path):
    upload_dir = tmp_path / "preview"
    upload_dir.mkdir()
    stale_file = upload_dir / "stale.xlsx"
    stale_file.write_bytes(b"x")
    fresh_file = upload_dir / "fresh.xlsx"
    fresh_file.write_bytes(b"x")
    stale_payload = {
        "file_path": str(stale_file),
        "file_name": "stale.xlsx",
        "metadata": _entry_payload(),
        "layout": "vertical",
        "header_row": 1,
        "source_rows": [],
        "source_columns": [],
        "source_mode": "headered",
        "warnings": [],
        "entries_preview": [],
        "invalid_rows": [],
        "total_records": 0,
        "duplicate_records": [],
        "skip_duplicate_indexes": [],
    }
    save_preview_session(str(upload_dir), "stale-token", stale_payload)
    session_file = upload_dir / "_preview_sessions" / "stale-token" / "session.json"
    with open(session_file, "r", encoding="utf-8") as f:
        stale_data = json.load(f)
    stale_data["created_at"] = 0
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(stale_data, f)

    fresh_payload = {
        **stale_payload,
        "file_name": "fresh.xlsx",
        "file_path": str(fresh_file),
    }
    save_preview_session(str(upload_dir), "fresh-token", fresh_payload)

    flask_session = {"upload_preview_token": "stale-token"}
    cleanup_upload_preview_cache(str(upload_dir), flask_session)

    assert "upload_preview_token" not in flask_session
    assert load_preview_session(str(upload_dir), "stale-token") is None
    assert load_preview_session(str(upload_dir), "fresh-token") is not None


def test_find_duplicate_entries_in_db_detects_existing_rows(db_path):
    row = {
        "uploader_name": "U1",
        "version": "v1",
        "template_type": "excel",
        "data_type": "flow",
        "time_period": "quarterly",
        "indicator_name": "GDP",
        "value": 1.0,
        "unit": None,
        "region_code": None,
        "year": 2024,
        "month": 1,
        "quarter": 1,
        "dataset_code": "",
    }
    models.insert_entries([row])
    found = find_duplicate_entries_in_db(
        "U1",
        "v1",
        [
            {
                "indicator_name": "GDP",
                "year": 2024,
                "month": 1,
                "quarter": 1,
                "dataset_code": "",
            }
        ],
    )
    assert len(found) == 1
    first = found[0]
    assert first["uploader_name"] == "U1"
    assert first["version"] == "v1"
    assert first["indicator_name"] == "GDP"
    assert first["year"] == 2024
    assert first["month"] == 1
    assert first["quarter"] == 1
    assert first["value"] == 1.0


def test_to_preview_context_returns_default_sample_count_and_duplicates():
    payload = {
        "file_name": "sample.xlsx",
        "layout": "vertical",
        "source_mode": "headered",
        "header_row": 1,
        "source_rows": [],
        "source_columns": [],
        "warnings": [],
        "entries_preview": [{"value": 1}],
        "invalid_rows": [],
        "total_records": 2,
        "duplicate_records": [
            {"indicator_name": "GDP", "year": 2024, "month": 3, "quarter": None},
        ],
    }
    ctx = to_preview_context(payload, skip_duplicate_indexes=["0"])
    assert ctx["sample_count"] == 1
    assert ctx["duplicate_records"] == payload["duplicate_records"]
    assert ctx["skip_duplicate_indexes"] == ["0"]
