# -*- coding: utf-8 -*-
"""Orchestrate post-persist side effects for successful Excel upload intake (audit + preview cleanup)."""
from __future__ import annotations

from typing import Any

from services.dataset_catalog import normalize_dataset_code
from services.upload_fs import safe_remove_upload_working_file
from services.upload_preview import delete_preview_session
from services.upload_runs import record_upload_run


def _safe_remove_file(path: str | None, *, upload_root: str | None = None) -> None:
    safe_remove_upload_working_file(path, upload_root=upload_root)


def finalize_successful_excel_upload_intake(
    *,
    entries: list[dict[str, Any]],
    token_metadata: dict[str, Any] | None,
    file_name: str | None,
    upload_folder: str | None,
    preview_token: str | None,
    working_file_path: str | None,
    message: str | None = None,
) -> None:
    """
    After rows are persisted: best-effort upload_runs row, drop preview session, remove working file.

    ``preview_token`` / ``upload_folder`` omitted → skip session cleanup (direct-save path).
    ``working_file_path`` omitted → skip file removal (caller may delete elsewhere).
    """
    if not entries:
        return
    meta = token_metadata or {}
    dataset_code = str(entries[0].get("dataset_code") or "") or normalize_dataset_code(
        meta.get("dataset_slug")
    )
    record_upload_run(
        uploader_name=entries[0]["uploader_name"],
        version=entries[0]["version"],
        dataset_code=dataset_code,
        file_name=file_name,
        status="success",
        message=message,
        row_count=len(entries),
    )
    if upload_folder and preview_token:
        delete_preview_session(upload_folder, preview_token)
    if working_file_path:
        _safe_remove_file(working_file_path, upload_root=upload_folder)
