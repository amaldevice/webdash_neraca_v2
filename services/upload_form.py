# -*- coding: utf-8 -*-
"""
Upload form helpers: form parsing, validation, and file persistence utilities.

These functions are extracted from upload_flow.py to separate form-handling
concerns from upload orchestration logic.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

from services.dataset_catalog import get_dataset_or_none
from services.validation import allowed_file, validate_metadata
from werkzeug.utils import secure_filename


def _form_getlist(form: Any, key: str) -> list[str]:
    gl = getattr(form, "getlist", None)
    if callable(gl):
        return [str(x) for x in gl(key)]
    raw = form.get(key)  # type: ignore[union-attr]
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw]
    return [str(raw)]


def normalize_upload_action(action: str) -> str:
    a = (action or "").strip().lower()
    if a not in {"preview", "save", "direct_upload"}:
        return "preview"
    return a


def parse_upload_form(form) -> tuple[dict[str, str], str, str, list[str]]:
    """Extract uploader metadata, action, preview token, duplicate skip list from POST form."""
    uploader = form.get("uploader", "").strip()
    version = form.get("version", "").strip()
    data_type = form.get("data_type", "flow").strip()
    time_period = form.get("time_period", "monthly").strip()
    dataset_slug = form.get("dataset_slug", "").strip()
    action = form.get("action", "preview").strip().lower()
    preview_token = form.get("preview_token", "").strip()
    form_values = {
        "uploader": uploader,
        "version": version,
        "data_type": data_type,
        "time_period": time_period,
        "layout_override": "auto",
        "dataset_slug": dataset_slug,
    }
    skip_dup = _form_getlist(form, "skip_duplicate_indexes")
    return form_values, action, preview_token, skip_dup


def collect_upload_file_errors(
    uploader: str,
    version: str,
    file,
    data_type: str,
    time_period: str,
    *,
    dataset_slug: str | None = None,
    require_dataset: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not uploader:
        errors.append("Nama pengunggah wajib diisi.")
    if not version:
        errors.append("Versi wajib diisi.")
    if not file or not allowed_file(file.filename):
        errors.append("Harus mengunggah file Excel (.xls/.xlsx).")
    if require_dataset and not (dataset_slug or "").strip():
        errors.append("Pilih dataset / tabel terlebih dahulu.")
    slug = (dataset_slug or "").strip()
    if slug and get_dataset_or_none(slug) is None:
        errors.append("Dataset tidak dikenal.")
    errors.extend(validate_metadata(data_type, time_period))
    return errors


def save_uploaded_excel(upload_folder: str, file) -> tuple[str, str, str]:
    """
    Persist upload to disk. Returns (destination_path, display_name, stored_basename).
    """
    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    os.makedirs(upload_folder, exist_ok=True)
    destination = os.path.join(upload_folder, filename)
    file.save(destination)
    display = file.filename or filename
    return destination, display, filename
