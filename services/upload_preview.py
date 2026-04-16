# -*- coding: utf-8 -*-
"""Excel upload preview cache (disk-backed for multi-worker), duplicate detection, template context."""
from __future__ import annotations

import json
import os
import shutil
import uuid
from typing import Any

from flask import session

from config import UPLOAD_PREVIEW_TTL_SECONDS
from models.queries import preview_duplicates_batches
from services.timeutil import utc_now_timestamp

# Back-compat: in-memory cache removed; kept as empty mapping for any legacy monkeypatches.
UPLOAD_PREVIEW_CACHE: dict[str, dict] = {}


def _sessions_root(upload_folder: str) -> str:
    return os.path.join(upload_folder, "_preview_sessions")


def _session_json_path(upload_folder: str, token: str) -> str:
    return os.path.join(_sessions_root(upload_folder), token, "session.json")


def _safe_remove_uploaded_file(upload_folder: str, file_path: str | None) -> None:
    if not file_path or not os.path.isfile(file_path):
        return
    try:
        uf = os.path.realpath(upload_folder)
        fp = os.path.realpath(file_path)
        if fp == uf or fp.startswith(uf + os.sep):
            os.remove(file_path)
    except OSError:
        pass


def _read_preview_session(upload_folder: str, token: str) -> dict | None:
    """Read one preview session payload from disk."""
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
    """Persist preview payload with created_at timestamp."""
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
    """Back-compat wrapper for writing preview payload."""
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
    """Collect unique duplicate-check keys from parsed entries (includes dataset_code)."""
    unique_keys: list[tuple] = []
    seen: set[tuple] = set()
    for entry in entries:
        ds = (entry.get("dataset_code") or entry.get("dataset_slug") or "").strip()
        key = (
            entry.get("indicator_name"),
            entry.get("year"),
            entry.get("month"),
            entry.get("quarter"),
            ds,
        )
        if key in seen:
            continue
        seen.add(key)
        unique_keys.append(key)
    return unique_keys


def _lookup_existing_duplicate_records(
    uploader: str,
    version: str,
    unique_keys: list[tuple],
) -> list[dict]:
    """Legacy helper: keep compatibility, now delegates to indicator+period matching."""
    return _lookup_existing_duplicate_records_by_indicator_period(unique_keys)


def find_duplicate_entries_in_db(
    _uploader: str | None = None,
    _version: str | None = None,
    entries: list[dict] | None = None,
) -> list[dict]:
    if entries is None:
        return []
    if not entries:
        return []
    unique_keys = _collect_duplicate_lookup_keys(entries)
    return _lookup_existing_duplicate_records_by_indicator_period(unique_keys)


def _lookup_existing_duplicate_records_by_indicator_period(unique_keys: list[tuple]) -> list[dict]:
    return preview_duplicates_batches(unique_keys)


def find_duplicate_entries_by_indicator_period(entries: list[dict]) -> list[dict]:
    if not entries:
        return []
    unique_keys = _collect_duplicate_lookup_keys(entries)
    return _lookup_existing_duplicate_records_by_indicator_period(unique_keys)


def filter_duplicate_entries(
    entries: list[dict],
    duplicate_records: list[dict],
    skip_indexes: set[int],
) -> tuple[list[dict], int]:
    duplicate_keys = [
        (
            duplicate.get("indicator_name"),
            duplicate.get("year"),
            duplicate.get("month"),
            duplicate.get("quarter"),
            (duplicate.get("dataset_code") or "").strip(),
        )
        for duplicate in duplicate_records
    ]
    skip_keys = {key for i, key in enumerate(duplicate_keys) if i in skip_indexes}
    deduped_entries: list[dict] = []
    skipped_count = 0
    for entry in entries:
        key = (
            entry.get("indicator_name"),
            entry.get("year"),
            entry.get("month"),
            entry.get("quarter"),
            (entry.get("dataset_code") or entry.get("dataset_slug") or "").strip(),
        )
        if key in skip_keys:
            skipped_count += 1
            continue
        deduped_entries.append(entry)
    return deduped_entries, skipped_count


def parse_selected_duplicate_indexes(
    raw_indexes: list[str],
    duplicate_records: list[dict],
) -> set[int]:
    selected_indexes: set[int] = set()
    max_index = len(duplicate_records)
    for raw_index in raw_indexes:
        try:
            idx = int(raw_index)
        except (TypeError, ValueError):
            continue
        if 0 <= idx < max_index:
            selected_indexes.add(idx)
    return selected_indexes


def cache_upload_preview(
    upload_folder: str,
    destination: str,
    file_name: str,
    metadata: dict,
    layout_override: str,
    payload: dict,
    duplicates: list[dict],
) -> str:
    upload_token = uuid.uuid4().hex
    old_token = session.get("upload_preview_token")
    if isinstance(old_token, str) and old_token != upload_token:
        _invalidate_preview_session(upload_folder, old_token)
    session_payload = _build_preview_session_payload(
        destination=destination,
        file_name=file_name,
        metadata=metadata,
        layout_override=layout_override,
        payload=payload,
        duplicates=duplicates,
    )
    save_preview_session(upload_folder, upload_token, session_payload)
    session["upload_preview_token"] = upload_token
    return upload_token


def _build_preview_session_payload(
    *,
    destination: str,
    file_name: str,
    metadata: dict[str, Any],
    layout_override: str,
    payload: dict,
    duplicates: list[dict],
) -> dict[str, Any]:
    return {
        "file_path": destination,
        "file_name": file_name,
        "metadata": metadata,
        "layout_override": layout_override,
        "layout": payload["layout"],
        "header_row": payload["header_row"],
        "source_rows": payload["source_rows"],
        "source_columns": payload["source_columns"],
        "source_mode": payload["source_mode"],
        "warnings": payload.get("warnings", []),
        "entries_preview": payload.get("sample", []),
        "invalid_rows": payload.get("invalid_rows", []),
        "total_records": len(payload.get("entries", [])),
        "duplicate_records": duplicates,
        "skip_duplicate_indexes": [],
    }


def excel_preview_source_from_payload(
    *,
    file_name: str,
    payload: dict,
    layout_override: str,
    upload_preview_token: str,
    total_records: int,
) -> dict:
    """
    Normalized dict for `to_preview_context` after a parse (confirm flow / fresh preview).
    Keeps upload_flow free of repeated OpenPyXL field wiring.
    """
    slug = (payload.get("dataset_slug") or "").strip()
    label = ""
    if slug:
        from services.dataset_catalog import get_dataset_or_none

        d = get_dataset_or_none(slug)
        if d is not None:
            label = d.label
    return {
        "file_name": file_name,
        "layout": payload["layout"],
        "source_mode": payload.get("source_mode", "headered"),
        "header_row": payload["header_row"],
        "source_rows": payload["source_rows"],
        "source_columns": payload["source_columns"],
        "layout_override": layout_override,
        "warnings": payload.get("warnings", []),
        "entries_preview": payload.get("sample", []),
        "invalid_rows": payload.get("invalid_rows", []),
        "total_records": total_records,
        "upload_preview_token": upload_preview_token,
        "dataset_slug": slug,
        "dataset_label": label,
    }


def to_preview_context(
    payload: dict,
    duplicates: list[dict] | None = None,
    skip_duplicate_indexes: list[str] | None = None,
) -> dict:
    return _to_template_context(payload, duplicates, skip_duplicate_indexes)


def _to_template_context(
    payload: dict,
    duplicates: list[dict] | None = None,
    skip_duplicate_indexes: list[str] | None = None,
) -> dict:
    duplicate_records = duplicates if duplicates is not None else payload.get("duplicate_records", [])
    if skip_duplicate_indexes is None:
        skip_duplicate_indexes = payload.get("skip_duplicate_indexes", [])
    return {
        "file_name": payload.get("file_name"),
        "layout": payload.get("layout"),
        "source_mode": payload.get("source_mode"),
        "header_row": payload.get("header_row"),
        "source_rows": payload.get("source_rows"),
        "source_columns": payload.get("source_columns"),
        "layout_override": payload.get("layout_override"),
        "warnings": payload.get("warnings", []),
        "entries_preview": payload.get("entries_preview", []),
        "sample_count": len(payload.get("entries_preview", [])),
        "invalid_rows": payload.get("invalid_rows", []),
        "total_records": payload.get("total_records"),
        "duplicate_records": duplicate_records,
        "skip_duplicate_indexes": skip_duplicate_indexes,
        "upload_preview_token": payload.get("upload_preview_token"),
        "dataset_slug": payload.get("dataset_slug", ""),
        "dataset_label": payload.get("dataset_label", ""),
    }


def build_upload_preview(
    *,
    upload_folder: str,
    destination: str,
    display_name: str,
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    layout_override: str,
    payload: dict,
    entries: list[dict],
    duplicates: list[dict],
    dataset_slug: str = "",
) -> tuple[str, dict]:
    """Create cached preview state and normalized preview context for templates."""
    effective_layout_override = layout_override or "auto"
    upload_token = cache_upload_preview(
        upload_folder,
        destination,
        display_name,
        {
            "uploader": uploader,
            "version": version,
            "data_type": data_type,
            "time_period": time_period,
            "dataset_slug": (dataset_slug or "").strip(),
        },
        effective_layout_override,
        payload,
        duplicates,
    )
    preview_payload = to_preview_context(
        excel_preview_source_from_payload(
            file_name=display_name,
            payload=payload,
            layout_override=layout_override or "auto",
            upload_preview_token=upload_token,
            total_records=len(entries),
        ),
        duplicates=duplicates,
        skip_duplicate_indexes=[],
    )
    return upload_token, preview_payload
