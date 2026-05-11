# -*- coding: utf-8 -*-
"""Parse Excel upload file and attach dataset_code + duplicate warnings (shared confirm/post paths)."""
from __future__ import annotations

from typing import Any

from excel_parser import parse_excel_payload
from excel_parser.constants import PREVIEW_SAMPLE_LIMIT

from services.dataset_catalog import normalize_dataset_code
from services.upload_duplicates import (
    _build_internal_duplicate_warning_message,
    _collect_internal_duplicate_counts,
)


def parse_and_validate_upload_payload(
    file_path: str,
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    *,
    layout_override: str = "auto",
    preview_limit: int = PREVIEW_SAMPLE_LIMIT,
    dataset_slug: str | None = None,
    require_dataset_context: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    """
    Parse payload from an uploaded file and return (payload, entries, warnings).

    Keperluan helper ini adalah membuat alur parse tetap konsisten antara
    proses confirm dan proses unggah file baru.
    """

    payload = parse_excel_payload(
        file_path,
        uploader,
        version,
        data_type,
        time_period,
        layout_override=layout_override,
        preview_limit=preview_limit,
        sheet_name=None,
        dataset_slug=dataset_slug,
        require_dataset_context=require_dataset_context,
    )
    entries = payload.get("entries", [])
    code = normalize_dataset_code(dataset_slug)
    for row in entries:
        row["dataset_code"] = code
    warnings = list(payload.get("warnings", []))
    internal_duplicate_warning = _build_internal_duplicate_warning_message(
        _collect_internal_duplicate_counts(entries)
    )
    if internal_duplicate_warning:
        warnings.append(internal_duplicate_warning)
    return payload, entries, warnings
