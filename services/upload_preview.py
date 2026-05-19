# -*- coding: utf-8 -*-
"""Excel upload preview cache (disk-backed for multi-worker), duplicate detection, template context."""
from __future__ import annotations

import json
import os
import shutil
import uuid
from typing import Any

from config import UPLOAD_PREVIEW_TTL_SECONDS
from models.queries import preview_duplicates_batches
from services.dataset_catalog import get_dataset_or_none
from services.timeutil import utc_now_timestamp
from services.upload_fs import safe_remove_upload_working_file


def _sessions_root(upload_folder: str) -> str:
    return os.path.join(upload_folder, "_preview_sessions")


def _session_json_path(upload_folder: str, token: str) -> str:
    return os.path.join(_sessions_root(upload_folder), token, "session.json")


def _safe_remove_uploaded_file(upload_folder: str, file_path: str | None) -> None:
    safe_remove_upload_working_file(file_path, upload_root=upload_folder)


def _read_preview_session(upload_folder: str, token: str) -> dict | None:
    if not token:
        return None
    path = _session_json_path(upload_folder, token)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _write_preview_session(upload_folder: str, token: str, payload: dict) -> None:
    root = _sessions_root(upload_folder)
    tdir = os.path.join(root, token)
    os.makedirs(tdir, exist_ok=True)
    out = {**payload, "created_at": utc_now_timestamp()}
    path = os.path.join(tdir, "session.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, default=str)


def _invalidate_preview_session(upload_folder: str, token: str) -> None:
    if not token:
        return
    data = _read_preview_session(upload_folder, token)
    file_path = None
    if isinstance(data, dict):
        file_path = data.get("file_path")
    _safe_remove_uploaded_file(upload_folder, file_path)
    tdir = os.path.join(_sessions_root(upload_folder), token)
    shutil.rmtree(tdir, ignore_errors=True)


def delete_preview_session(upload_folder: str, token: str) -> None:
    _invalidate_preview_session(upload_folder, token)


def load_preview_session(upload_folder: str, token: str) -> dict | None:
    data = _read_preview_session(upload_folder, token)
    if not isinstance(data, dict):
        return None
    try:
        created = float(data.get("created_at", 0))
    except (TypeError, ValueError):
        delete_preview_session(upload_folder, token)
        return None
    if utc_now_timestamp() - created > UPLOAD_PREVIEW_TTL_SECONDS:
        delete_preview_session(upload_folder, token)
        return None
    return data


def save_preview_session(upload_folder: str, token: str, payload: dict) -> None:
    _write_preview_session(upload_folder, token, payload)


def cleanup_upload_preview_cache(upload_folder: str, flask_session=None) -> None:
    root = _sessions_root(upload_folder)
    if not os.path.isdir(root):
        if flask_session is not None:
            _drop_stale_session_token(flask_session, upload_folder)
        return
    now = utc_now_timestamp()
    for name in list(os.listdir(root)):
        tokendir = os.path.join(root, name)
        sess_path = os.path.join(tokendir, "session.json")
        if not os.path.isfile(sess_path):
            shutil.rmtree(tokendir, ignore_errors=True)
            continue
        session_data = _read_preview_session(upload_folder, name)
        if not isinstance(session_data, dict):
            _invalidate_preview_session(upload_folder, name)
            continue
        try:
            created = float(session_data.get("created_at", 0))
            if now - created > UPLOAD_PREVIEW_TTL_SECONDS:
                _invalidate_preview_session(upload_folder, name)
        except ValueError:
            _invalidate_preview_session(upload_folder, name)
    if flask_session is not None:
        _drop_stale_session_token(flask_session, upload_folder)


def _drop_stale_session_token(flask_session, upload_folder: str) -> None:
    tok = flask_session.get("upload_preview_token")
    if isinstance(tok, str) and load_preview_session(upload_folder, tok) is None:
        flask_session.pop("upload_preview_token", None)


def _collect_duplicate_lookup_keys(entries: list[dict]) -> list[tuple]:
    unique_keys: list[tuple] = []
    seen: set[tuple] = set()
    for entry in entries:
        ds = (entry.get("dataset_code") or entry.get("dataset_slug") or "").strip()
        key = (entry.get("indicator_name"), entry.get("year"), entry.get("month"), entry.get("quarter"), ds)
        if key in seen:
            continue
        seen.add(key)
        unique_keys.append(key)
    return unique_keys


def find_duplicate_entries_in_db(_uploader=None, _version=None, entries=None):
    if entries is None:
        return []
    if not entries:
        return []
    return _lookup_existing_duplicate_records_by_indicator_period(_collect_duplicate_lookup_keys(entries))


def _lookup_existing_duplicate_records_by_indicator_period(unique_keys):
    return preview_duplicates_batches(unique_keys)


def find_duplicate_entries_by_indicator_period(entries):
    if not entries:
        return []
    return _lookup_existing_duplicate_records_by_indicator_period(_collect_duplicate_lookup_keys(entries))


def filter_duplicate_entries(entries, duplicate_records, skip_indexes):
    duplicate_keys = [
        (d.get("indicator_name"), d.get("year"), d.get("month"), d.get("quarter"), (d.get("dataset_code") or "").strip())
        for d in duplicate_records
    ]
    skip_keys = {key for i, key in enumerate(duplicate_keys) if i in skip_indexes}
    deduped: list[dict] = []
    skipped = 0
    for entry in entries:
        key = (entry.get("indicator_name"), entry.get("year"), entry.get("month"), entry.get("quarter"),
               (entry.get("dataset_code") or entry.get("dataset_slug") or "").strip())
        if key in skip_keys:
            skipped += 1
            continue
        deduped.append(entry)
    return deduped, skipped


def parse_selected_duplicate_indexes(raw_indexes, duplicate_records):
    selected: set[int] = set()
    max_index = len(duplicate_records)
    for raw in raw_indexes:
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            continue
        if 0 <= idx < max_index:
            selected.add(idx)
    return selected


def cache_upload_preview(
    upload_folder: str,
    destination: str,
    file_name: str,
    metadata: dict,
    payload: dict,
    duplicates: list[dict],
    old_token: str | None = None,
) -> str:
    upload_token = uuid.uuid4().hex
    if isinstance(old_token, str) and old_token != upload_token:
        _invalidate_preview_session(upload_folder, old_token)
    session_payload = _build_preview_session_payload(
        destination=destination, file_name=file_name, metadata=metadata, payload=payload, duplicates=duplicates,
    )
    save_preview_session(upload_folder, upload_token, session_payload)
    return upload_token


def _build_preview_session_payload(*, destination, file_name, metadata, payload, duplicates):
    return {
        "file_path": destination, "file_name": file_name, "metadata": metadata,
        "layout": payload["layout"], "header_row": payload["header_row"],
        "source_rows": payload["source_rows"], "source_columns": payload["source_columns"],
        "source_mode": payload["source_mode"], "warnings": payload.get("warnings", []),
        "entries_preview": payload.get("sample", []), "invalid_rows": payload.get("invalid_rows", []),
        "total_records": len(payload.get("entries", [])), "duplicate_records": duplicates, "skip_duplicate_indexes": [],
    }


def excel_preview_source_from_payload(*, file_name, payload, upload_preview_token, total_records):
    slug = (payload.get("dataset_slug") or "").strip()
    label = ""
    if slug:
        d = get_dataset_or_none(slug)
        if d is not None:
            label = d.label
    return {
        "file_name": file_name, "layout": payload["layout"],
        "source_mode": payload.get("source_mode", "headered"), "header_row": payload["header_row"],
        "source_rows": payload["source_rows"], "source_columns": payload["source_columns"],
        "warnings": payload.get("warnings", []), "entries_preview": payload.get("sample", []),
        "invalid_rows": payload.get("invalid_rows", []), "total_records": total_records,
        "upload_preview_token": upload_preview_token, "dataset_slug": slug, "dataset_label": label,
    }


def upload_page_preview_from_session(session_payload, *, upload_preview_token):
    meta = session_payload.get("metadata") or {}
    slug = (meta.get("dataset_slug") or "").strip()
    label = ""
    if slug:
        d = get_dataset_or_none(slug)
        if d is not None:
            label = d.label
    src = {
        "file_name": session_payload.get("file_name"), "layout": session_payload["layout"],
        "source_mode": session_payload.get("source_mode", "headered"), "header_row": session_payload["header_row"],
        "source_rows": session_payload["source_rows"], "source_columns": session_payload["source_columns"],
        "warnings": session_payload.get("warnings", []), "entries_preview": session_payload.get("entries_preview", []),
        "invalid_rows": session_payload.get("invalid_rows", []), "total_records": session_payload.get("total_records"),
        "upload_preview_token": upload_preview_token,
        "dataset_slug": slug, "dataset_label": label,
    }
    return to_preview_context(src, duplicates=session_payload.get("duplicate_records"),
                              skip_duplicate_indexes=session_payload.get("skip_duplicate_indexes") or [])


def to_preview_context(payload, duplicates=None, skip_duplicate_indexes=None):
    return _to_template_context(payload, duplicates, skip_duplicate_indexes)


def _to_template_context(payload, duplicates=None, skip_duplicate_indexes=None):
    duplicate_records = duplicates if duplicates is not None else payload.get("duplicate_records", [])
    if skip_duplicate_indexes is None:
        skip_duplicate_indexes = payload.get("skip_duplicate_indexes", [])
    return {
        "file_name": payload.get("file_name"), "layout": payload.get("layout"),
        "source_mode": payload.get("source_mode"), "header_row": payload.get("header_row"),
        "source_rows": payload.get("source_rows"), "source_columns": payload.get("source_columns"),
        "warnings": payload.get("warnings", []), "entries_preview": payload.get("entries_preview", []),
        "sample_count": len(payload.get("entries_preview", [])), "invalid_rows": payload.get("invalid_rows", []),
        "total_records": payload.get("total_records"), "duplicate_records": duplicate_records,
        "skip_duplicate_indexes": skip_duplicate_indexes, "upload_preview_token": payload.get("upload_preview_token"),
        "dataset_slug": payload.get("dataset_slug", ""), "dataset_label": payload.get("dataset_label", ""),
    }


def build_upload_preview(*, upload_folder, destination, display_name, uploader, version,
                         data_type, time_period, payload, entries, duplicates,
                         dataset_slug="", old_token=None):
    upload_token = cache_upload_preview(
        upload_folder, destination, display_name,
        {"uploader": uploader, "version": version, "data_type": data_type,
         "time_period": time_period, "dataset_slug": (dataset_slug or "").strip()},
        payload, duplicates, old_token=old_token,
    )
    session_data = load_preview_session(upload_folder, upload_token) or {}
    preview_payload = upload_page_preview_from_session(session_data, upload_preview_token=upload_token)
    return upload_token, preview_payload
