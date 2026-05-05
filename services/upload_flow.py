# -*- coding: utf-8 -*-
"""
Excel upload orchestration: validation, confirm-from-session, and post-parse branches.

HTTP (flash, redirect, session) stays in `routes/upload_routes`; this module returns structured
results. Preview disk I/O and duplicate checks live in `services.upload_preview`.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any

from sqlalchemy.exc import IntegrityError as SAIntegrityError
from excel_parser.constants import PREVIEW_SAMPLE_LIMIT

from excel_parser import parse_excel_payload
from models import upsert_entries
from services.db_errors import is_duplicate_key_error, resolve_duplicate_check_dialect
from services.dataset_catalog import get_dataset_or_none, normalize_dataset_code
from services.manual_entries import build_manual_entry
from services.upload_duplicates import (
    _build_internal_duplicate_warning_message,
    _collect_internal_duplicate_counts,
    _hydrate_duplicate_records_with_values,
)
from services.upload_handlers import (
    _safe_remove_file,
    handle_upload_confirm_with_duplicates,
    handle_upload_confirm_without_duplicates,
    handle_upload_post_file_no_entries,
    handle_upload_post_file_preview,
    handle_upload_post_file_save_with_duplicates,
    handle_upload_post_file_save_without_duplicates,
)
from services.upload_preview import (
    find_duplicate_entries_by_indicator_period,
    find_duplicate_entries_in_db,
    load_preview_session,
    delete_preview_session,
    cache_upload_preview,
)
from services.upload_runs import record_upload_run
from services.upload_types import (
    ManualFlowResponse,
    UploadFlowResponse,
    build_upload_response,
)
from services.upload_form import (
    collect_upload_file_errors,
    normalize_upload_action,
    parse_upload_form,
    save_uploaded_excel,
)
from services.validation import validate_metadata

UPLOAD_TEMPLATE_NAME = "upload.html"
UPLOAD_ROUTE_MODE = "upload"
MANUAL_ROUTE_MODE = "manual"


def upload_folder_from_config(config: dict) -> str:
    """Resolve configured upload directory (shared disk for multi-worker preview sessions)."""
    return config["UPLOAD_FOLDER"]


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


def process_upload_confirm(
    upload_folder: str,
    preview_token: str,
    form_values: dict[str, str],
    skip_duplicate_indexes_raw: list[str],
    *,
    require_dataset: bool = False,
) -> UploadFlowResponse:
    """
    Handle POST action=confirm.

    Contract:
      Input:
        - upload_folder: direktori penyimpanan sesi file preview.
        - preview_token: token sesi preview yang dibuat saat `build_upload_preview`.
      - form_values: metadata formulir wajib (uploader/version/data_type/time_period/dataset_slug).
        - skip_duplicate_indexes_raw: daftar index yang disetujui untuk menolak duplikasi.
      Output:
        - UploadFlowResponse.kind:
          - "redirect" untuk alur sukses/eror utama.
          - "render" untuk menampilkan ulang preview ketika ada konflik/validasi.
        - Flashes berisi pesan manusia.
        - preview dan upload_preview_token hanya diisi saat branch render.
        - pop_upload_session_token True pada redirect sukses setelah insert/pembersihan.
    """
    token_payload = load_preview_session(upload_folder, preview_token) or {}
    if not token_payload:
        return build_upload_response(
            "redirect",
            [("Sesi pratinjau tidak ditemukan atau telah kedaluwarsa.", "error")],
        )

    meta = token_payload["metadata"]
    file_path = token_payload["file_path"]
    slug = (meta.get("dataset_slug") or "").strip()
    try:
        payload, entries, _ = parse_and_validate_upload_payload(
            file_path,
            meta["uploader"],
            meta["version"],
            meta["data_type"],
            meta["time_period"],
            layout_override="auto",
            preview_limit=PREVIEW_SAMPLE_LIMIT,
            dataset_slug=slug or None,
            require_dataset_context=require_dataset,
        )
    except Exception as e:
        return build_upload_response(
            "redirect",
            [(f"Gagal memproses berkas pratinjau: {str(e)}", "error")],
        )
    internal_duplicate_warning = _build_internal_duplicate_warning_message(
        _collect_internal_duplicate_counts(entries)
    )
    if internal_duplicate_warning:
        return build_upload_response("redirect", [(internal_duplicate_warning, "error")])
    if not entries:
        msg = "Sesi pratinjau tidak memuat data valid."
        joined = " ".join(str(w) for w in (payload.get("warnings") or []) if w)
        if require_dataset and slug and "dataset_slug wajib" in joined:
            msg = "Dataset wajib dipilih untuk pratinjau ini, tetapi metadata sesi tidak lengkap. Unggah ulang dengan dataset yang sama."
        return build_upload_response("redirect", [(msg, "error")])

    duplicates = _hydrate_duplicate_records_with_values(
        find_duplicate_entries_in_db(meta["uploader"], meta["version"], entries),
        entries,
    )
    if duplicates:
        return handle_upload_confirm_with_duplicates(
            upload_folder=upload_folder,
            preview_token=preview_token,
            file_path=file_path,
            parse_payload=payload,
            token_payload=token_payload,
            entries=entries,
            duplicates=duplicates,
            skip_duplicate_indexes_raw=skip_duplicate_indexes_raw,
            form_values=form_values,
        )

    return handle_upload_confirm_without_duplicates(
        upload_folder=upload_folder,
        file_path=file_path,
        preview_token=preview_token,
        entries=entries,
        token_payload=token_payload,
    )


def process_upload_post_file(
    upload_folder: str,
    destination: str,
    display_name: str,
    form_values: dict[str, str],
    action: str,
    *,
    require_dataset: bool = False,
) -> UploadFlowResponse:
    """
    Setelah file multipart tersimpan: parse Excel lalu pilih alur preview / simpan.

    Contract:
      Input:
        - upload_folder: lokasi disk untuk sesi preview.
        - destination: path file yang baru disimpan.
        - display_name: nama file asli dari user.
        - form_values: metadata uploader/version/data_type/time_period/dataset_slug.
        - action: 'preview' | 'save' | 'direct_upload'.
      Output:
        - UploadFlowResponse.kind:
          - "render" untuk tampilkan preview + flash info.
          - "redirect" jika tersimpan langsung (tanpa konflik duplikasi).
        - Selalu bersihin file fisik kalau parsing gagal.
        - Untuk alur berhasil simpan direct, file sumber akan dihapus.
    """
    uploader = form_values["uploader"]
    version = form_values["version"]
    data_type = form_values["data_type"]
    time_period = form_values["time_period"]
    slug = (form_values.get("dataset_slug") or "").strip()

    try:
        payload, entries, warnings = parse_and_validate_upload_payload(
            destination,
            uploader,
            version,
            data_type,
            time_period,
            layout_override="auto",
            preview_limit=PREVIEW_SAMPLE_LIMIT,
            dataset_slug=slug or None,
            require_dataset_context=require_dataset,
        )
    except Exception as e:
        _safe_remove_file(destination)
        return build_upload_response(
            "render",
            [(f"Gagal membaca berkas Excel: {str(e)}", "error")],
            preview=None,
            upload_preview_token=None,
            form_values=form_values,
        )

    if not entries:
        return handle_upload_post_file_no_entries(destination, form_values, warnings)
    internal_duplicate_warning = _build_internal_duplicate_warning_message(
        _collect_internal_duplicate_counts(entries)
    )
    if internal_duplicate_warning:
        extra_flashes = [(internal_duplicate_warning, "error")]
        extra_flashes.extend(
            (warning, "warning") for warning in warnings if warning != internal_duplicate_warning
        )
        return build_upload_response(
            "render",
            extra_flashes,
            preview=None,
            upload_preview_token=None,
            form_values=form_values,
        )

    duplicates = _hydrate_duplicate_records_with_values(
        find_duplicate_entries_in_db(uploader, version, entries),
        entries,
    )
    if action == "save":
        if duplicates:
            return handle_upload_post_file_save_with_duplicates(
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
                form_values=form_values,
            )

        try:
            response = handle_upload_post_file_save_without_duplicates(
                entries, form_values, source_file_name=display_name
            )
            if response.kind == "redirect":
                if os.path.exists(destination):
                    _safe_remove_file(destination)
                return response
            return response
        except Exception as e:
            return build_upload_response(
                "render",
                [(f"Terjadi kesalahan saat menyimpan data: {str(e)}", "error")],
                preview=None,
                upload_preview_token=None,
                form_values=form_values,
            )

    return handle_upload_post_file_preview(
        upload_folder=upload_folder,
        destination=destination,
        display_name=display_name,
        form_values=form_values,
        payload=payload,
        entries=entries,
        duplicates=duplicates,
    )


def process_manual_input_post(
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    period_date: str,
    indicator: str,
    value: str,
    confirm_duplicate: bool = False,
    *,
    dataset_slug: str = "",
    require_dataset: bool = False,
) -> ManualFlowResponse:
    form_values: dict[str, str] = {
        "uploader": uploader,
        "version": version,
        "data_type": data_type,
        "time_period": time_period,
        "period_date": period_date,
        "indicator": indicator,
        "value": value,
        "dataset_slug": (dataset_slug or "").strip(),
    }
    if require_dataset and not (dataset_slug or "").strip():
        return ManualFlowResponse(
            kind="render",
            flashes=[("Pilih dataset / tabel terlebih dahulu.", "error")],
            form_values=form_values,
        )
    ds = (dataset_slug or "").strip()
    if ds and get_dataset_or_none(ds) is None:
        return ManualFlowResponse(
            kind="render",
            flashes=[("Dataset tidak dikenal.", "error")],
            form_values=form_values,
        )
    if not uploader or not version or not indicator or not value or not period_date:
        return ManualFlowResponse(
            kind="render",
            flashes=[("Semua kolom metadata dan data wajib diisi.", "error")],
            form_values=form_values,
        )
    validation_errors = validate_metadata(data_type, time_period)
    if validation_errors:
        return ManualFlowResponse(
            kind="render",
            flashes=[(e, "error") for e in validation_errors],
            form_values=form_values,
        )
    manual_entry = build_manual_entry(
        uploader,
        version,
        data_type,
        time_period,
        period_date,
        indicator,
        value,
        dataset_slug=ds,
    )
    if manual_entry is None:
        return ManualFlowResponse(
            kind="render",
            flashes=[("Nilai indikator tidak valid.", "error")],
            form_values=form_values,
        )

    duplicates = find_duplicate_entries_by_indicator_period([manual_entry])
    if duplicates and not confirm_duplicate:
        period = (
            f"{manual_entry['year']}-{manual_entry['month']:02d}"
            if manual_entry["month"]
            else (
                f"{manual_entry['year']}-Q{manual_entry['quarter']}"
                if manual_entry["quarter"]
                else str(manual_entry["year"])
            )
        )
        return ManualFlowResponse(
            kind="render",
            flashes=[
                (
                    f"Ditemukan {len(duplicates)} data existing dengan kunci indikator + periode "
                    f"({manual_entry['indicator_name']} / {period}). "
                    "Konfirmasi ulang untuk tetap menyimpan entri manual.",
                    "warning",
                )
            ],
            form_values=form_values,
            manual_duplicate={
                "exists": True,
                "indicator": manual_entry["indicator_name"],
                "period": period,
                "count": len(duplicates),
                "existing_records": duplicates,
            },
        )

    try:
        upsert_entries([manual_entry])
        record_upload_run(
            uploader_name=manual_entry["uploader_name"],
            version=manual_entry["version"],
            dataset_code=str(manual_entry.get("dataset_code") or ""),
            file_name=None,
            status="success",
            message="manual_input",
            row_count=1,
        )
        return ManualFlowResponse(
            kind="redirect",
            flashes=[("Entri manual berhasil dicatat dan disimpan.", "success")],
            form_values=form_values,
        )
    except (sqlite3.IntegrityError, SAIntegrityError) as exc:
        flash_msg = (
            "Data duplikat: kombinasi pengunggah, versi, indikator, periode, dan waktu sudah ada.\n"
            if is_duplicate_key_error(exc, resolve_duplicate_check_dialect())
            else f"Terjadi kesalahan database: {exc}"
        )
        return ManualFlowResponse(
            kind="render",
            flashes=[(flash_msg, "error")],
            form_values=form_values,
        )
