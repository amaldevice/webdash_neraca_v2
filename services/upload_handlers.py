# -*- coding: utf-8 -*-
"""
Upload branch handlers; persistence lives in `services.upload_commit`.

Each handler implements one specific branch of the upload flow
(confirm-with-duplicates, save-without-duplicates, preview, etc.).
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any

from sqlalchemy.exc import IntegrityError as SAIntegrityError

from services.upload_commit import (
    persist_upload_entries,
    persist_upload_entries_with_overwrite,
)
from services.db_errors import is_duplicate_key_error, resolve_duplicate_check_dialect
from services.upload_intake_finalize import (
    _safe_remove_file,
    finalize_successful_excel_upload_intake,
)
from services.upload_duplicates import (
    _build_duplicate_confirmation_summary,
    _duplicate_conflict_message,
    prepare_duplicate_plan,
)
from services.upload_types import UploadFlowResponse, build_upload_response
from services.upload_preview import (
    build_upload_preview,
    cache_upload_preview,
    excel_preview_source_from_payload,
    to_preview_context,
)

def handle_upload_confirm_with_duplicates(
    upload_folder: str,
    preview_token: str,
    file_path: str,
    parse_payload: dict[str, Any],
    token_payload: dict[str, Any],
    entries: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
    skip_duplicate_indexes_raw: list[str],
    form_values: dict[str, str],
) -> UploadFlowResponse:
    selected_indexes, selected_indexes_payload, deduped_entries, skipped_count = prepare_duplicate_plan(
        entries=entries,
        duplicates=duplicates,
        skip_duplicate_indexes_raw=skip_duplicate_indexes_raw,
    )
    _, overwrite_count, safe_rows_count = _build_duplicate_confirmation_summary(
        duplicates,
        selected_indexes,
        deduped_entries,
    )

    metadata = token_payload.get("metadata", {})
    form_values = {
        "uploader": form_values.get("uploader", metadata.get("uploader", "")),
        "version": form_values.get("version", metadata.get("version", "")),
        "data_type": form_values.get("data_type", metadata.get("data_type", "")),
        "time_period": form_values.get("time_period", metadata.get("time_period", "")),
        "dataset_slug": form_values.get("dataset_slug", metadata.get("dataset_slug", "")),
    }
    if not deduped_entries:
        preview_payload = to_preview_context(
            excel_preview_source_from_payload(
                file_name=token_payload.get("file_name", ""),
                payload=parse_payload,
                upload_preview_token=preview_token,
                total_records=len(entries),
            ),
            duplicates=duplicates,
            skip_duplicate_indexes=selected_indexes_payload,
        )
        return build_upload_response(
            "render",
            [("Semua baris pada file adalah duplikasi terpilih. Tidak ada data baru untuk disimpan.", "warning")],
            preview=preview_payload,
            upload_preview_token=preview_token,
            form_values=form_values,
        )
    try:
        persist_upload_entries_with_overwrite(deduped_entries)
        finalize_successful_excel_upload_intake(
            entries=deduped_entries,
            token_metadata=metadata,
            file_name=token_payload.get("file_name"),
            upload_folder=upload_folder,
            preview_token=preview_token,
            working_file_path=file_path,
            message="overwrite_confirm",
        )

        if overwrite_count > 0 and skipped_count > 0:
            msg = (
                f"{len(deduped_entries)} baris disimpan, {overwrite_count} baris duplikasi ditimpa, "
                f"{skipped_count} baris duplikasi dikecualikan."
            )
        elif overwrite_count > 0:
            msg = f"{len(deduped_entries)} baris disimpan, {overwrite_count} baris duplikasi ditimpa."
        elif safe_rows_count > 0:
            msg = f"{len(deduped_entries)} baris disimpan."
        else:
            msg = f"{len(deduped_entries)} baris data berhasil disimpan."

        flashes: list[tuple[str, str]] = []
        if overwrite_count > 0:
            overwrite_warning = (
                f"PERINGATAN: {overwrite_count} baris duplikasi (kunci unik sama) ditimpa sesuai pilihan saat ini."
                if len(duplicates) == 1
                else f"PERINGATAN: {overwrite_count} baris duplikasi (kunci unik sama) akan ditimpa sesuai pilihan saat ini."
            )
            flashes.append((overwrite_warning, "warning"))
            if skipped_count > 0:
                flashes.append((f"{skipped_count} baris duplikasi lainnya dikecualikan.", "warning"))
        else:
            flashes.append((f"{skipped_count} baris duplikasi dikecualikan.", "warning"))
        flashes.append((msg, "success"))
        return build_upload_response(
            "redirect",
            flashes,
            pop_upload_session_token=True,
        )
    except (sqlite3.IntegrityError, SAIntegrityError) as e:
        error_msg = str(e)
        if is_duplicate_key_error(e, resolve_duplicate_check_dialect()):
            flash_msg = _duplicate_conflict_message()
        else:
            flash_msg = f"Terjadi kesalahan database: {error_msg}"
        return build_upload_response("redirect", [(flash_msg, "error")])
    except Exception as e:
        return build_upload_response(
            "redirect",
            [(f"Terjadi kesalahan saat menyimpan data: {str(e)}", "error")],
        )


def handle_upload_confirm_without_duplicates(
    upload_folder: str,
    file_path: str,
    preview_token: str,
    entries: list[dict[str, Any]],
    *,
    token_payload: dict[str, Any] | None = None,
) -> UploadFlowResponse:
    try:
        persist_upload_entries(entries)
        finalize_successful_excel_upload_intake(
            entries=entries,
            token_metadata=(token_payload or {}).get("metadata") or {},
            file_name=(token_payload or {}).get("file_name"),
            upload_folder=upload_folder,
            preview_token=preview_token,
            working_file_path=file_path,
        )
        return build_upload_response(
            "redirect",
            [(f"{len(entries)} baris data berhasil disimpan.", "success")],
            pop_upload_session_token=True,
        )
    except (sqlite3.IntegrityError, SAIntegrityError) as e:
        error_msg = str(e)
        if is_duplicate_key_error(e, resolve_duplicate_check_dialect()):
            flash_msg = _duplicate_conflict_message()
        else:
            flash_msg = f"Terjadi kesalahan database: {error_msg}"
        return build_upload_response("redirect", [(flash_msg, "error")])
    except Exception as e:
        return build_upload_response(
            "redirect",
            [(f"Terjadi kesalahan saat menyimpan data: {str(e)}", "error")],
        )


def handle_upload_post_file_no_entries(
    destination: str,
    form_values: dict[str, str],
    warnings: list[str],
) -> UploadFlowResponse:
    flashes: list[tuple[str, str]] = []
    for warning in warnings:
        flashes.append((warning, "warning"))
    if not warnings:
        flashes.append(("File Excel tidak berisi data yang valid.", "error"))
    if os.path.exists(destination):
        _safe_remove_file(destination)
    return build_upload_response(
        "render",
        flashes,
        preview=None,
        upload_preview_token=None,
        form_values=form_values,
    )


def handle_upload_post_file_save_with_duplicates(
    upload_folder: str,
    destination: str,
    display_name: str,
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    payload: dict[str, Any],
    entries: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
    form_values: dict[str, str],
) -> UploadFlowResponse:
    upload_token, preview_payload = build_upload_preview(
        upload_folder=upload_folder,
        destination=destination,
        display_name=display_name,
        uploader=uploader,
        version=version,
        data_type=data_type,
        time_period=time_period,
        payload=payload,
        entries=entries,
        duplicates=duplicates,
        dataset_slug=form_values.get("dataset_slug", ""),
    )
    return build_upload_response(
        "render",
        [
            (
                f"Ditemukan {len(duplicates)} baris duplikasi dengan data yang sudah ada. "
                "Pada pratinjau, tandai baris yang ingin dikecualikan sebelum simpan; "
                "baris lain dapat menimpa data lama.",
                "warning",
            )
        ],
        preview=preview_payload,
        upload_preview_token=upload_token,
        form_values=form_values,
    )


def handle_upload_post_file_save_without_duplicates(
    entries: list[dict[str, Any]],
    form_values: dict[str, str],
    *,
    source_file_name: str = "",
) -> UploadFlowResponse:
    try:
        persist_upload_entries(entries)
        finalize_successful_excel_upload_intake(
            entries=entries,
            token_metadata=None,
            file_name=source_file_name or None,
            upload_folder=None,
            preview_token=None,
            working_file_path=None,
        )
        return build_upload_response(
            "redirect",
            [(f"{len(entries)} baris data berhasil disimpan.", "success")],
        )
    except (sqlite3.IntegrityError, SAIntegrityError) as e:
        error_msg = str(e)
        if is_duplicate_key_error(e, resolve_duplicate_check_dialect()):
            flash_msg = _duplicate_conflict_message()
        else:
            flash_msg = f"Terjadi kesalahan database: {error_msg}"
        return build_upload_response(
            "render",
            [(flash_msg, "error")],
            preview=None,
            upload_preview_token=None,
            form_values=form_values,
        )
    except Exception as e:
        return build_upload_response(
            "render",
            [(f"Terjadi kesalahan saat menyimpan data: {str(e)}", "error")],
            preview=None,
            upload_preview_token=None,
            form_values=form_values,
        )


def handle_upload_post_file_preview(
    upload_folder: str,
    destination: str,
    display_name: str,
    form_values: dict[str, str],
    payload: dict[str, Any],
    entries: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
) -> UploadFlowResponse:
    metadata = {
        "uploader": form_values["uploader"],
        "version": form_values["version"],
        "data_type": form_values["data_type"],
        "time_period": form_values["time_period"],
        "dataset_slug": form_values.get("dataset_slug", ""),
    }
    upload_token = cache_upload_preview(
        upload_folder,
        destination,
        display_name,
        metadata,
        payload,
        duplicates,
    )
    preview_payload = to_preview_context(
        excel_preview_source_from_payload(
            file_name=display_name,
            payload=payload,
            upload_preview_token=upload_token,
            total_records=len(entries),
        ),
        duplicates=duplicates,
        skip_duplicate_indexes=[],
    )
    if duplicates:
        info_flash = (
            f"Ditemukan {len(duplicates)} baris yang sudah ada di basis data. "
            "Jika dilanjutkan, baris duplikasi akan ditimpa sesuai kebijakan penyimpanan.",
            "warning",
        )
    else:
        info_flash = ("Klik tombol konfirmasi untuk menyimpan data yang sudah dipratinjau.", "info")
    return build_upload_response(
        "render",
        [info_flash],
        preview=preview_payload,
        upload_preview_token=upload_token,
        form_values=form_values,
    )
