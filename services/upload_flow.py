# -*- coding: utf-8 -*-
"""
Excel upload orchestration: validation, confirm-from-session, and post-parse branches.

HTTP (flash, redirect, session) stays in `routes/upload_routes`; this module returns structured
results. Preview disk I/O and duplicate checks live in `services.upload_preview`.
"""
from __future__ import annotations

import os
import sqlite3
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from excel_parser import parse_excel_payload
from models import insert_entries
from services.aggregation import refresh_aggregated_summary
from services.manual_entries import build_manual_entry
from services.upload_preview import (
    build_upload_preview,
    cache_upload_preview,
    delete_preview_session,
    excel_preview_source_from_payload,
    filter_duplicate_entries,
    find_duplicate_entries_in_db,
    load_preview_session,
    parse_selected_duplicate_indexes,
    to_preview_context,
)
from services.validation import allowed_file, validate_metadata
from werkzeug.utils import secure_filename

UPLOAD_TEMPLATE_NAME = "upload.html"
UPLOAD_ROUTE_MODE = "upload"
MANUAL_ROUTE_MODE = "manual"


def upload_folder_from_config(config: dict) -> str:
    """Resolve configured upload directory (shared disk for multi-worker preview sessions)."""
    return config["UPLOAD_FOLDER"]


def normalize_upload_action(action: str) -> str:
    a = (action or "").strip().lower()
    if a not in {"preview", "save", "direct_upload"}:
        return "preview"
    return a


@dataclass
class UploadFlowResponse:
    """Route applies `flashes` then either renders upload template or redirects to upload_data."""

    kind: Literal["render", "redirect"]
    flashes: list[tuple[str, str]] = field(default_factory=list)
    preview: dict[str, Any] | None = None
    upload_preview_token: str | None = None
    form_values: dict[str, Any] | None = None
    pop_upload_session_token: bool = False


@dataclass
class ManualFlowResponse:
    kind: Literal["render", "redirect"]
    flashes: list[tuple[str, str]] = field(default_factory=list)


def parse_upload_form(form) -> tuple[dict[str, str], str, str, list[str]]:
    """Extract uploader metadata, action, preview token, duplicate skip list from POST form."""
    uploader = form.get("uploader", "").strip()
    version = form.get("version", "").strip()
    data_type = form.get("data_type", "flow").strip()
    time_period = form.get("time_period", "monthly").strip()
    layout_override = form.get("layout_override", "auto").strip().lower()
    action = form.get("action", "preview").strip().lower()
    preview_token = form.get("preview_token", "").strip()
    form_values = {
        "uploader": uploader,
        "version": version,
        "data_type": data_type,
        "time_period": time_period,
        "layout_override": layout_override,
    }
    skip_dup = form.getlist("skip_duplicate_indexes")
    return form_values, action, preview_token, skip_dup


def collect_upload_file_errors(
    uploader: str,
    version: str,
    file,
    data_type: str,
    time_period: str,
) -> list[str]:
    errors: list[str] = []
    if not uploader:
        errors.append("Nama pengunggah wajib diisi.")
    if not version:
        errors.append("Versi wajib diisi.")
    if not file or not allowed_file(file.filename):
        errors.append("Harus mengunggah file Excel (.xls/.xlsx).")
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


def parse_and_validate_upload_payload(
    file_path: str,
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    *,
    layout_override: str = "auto",
    preview_limit: int = 0,
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
    )
    return payload, payload.get("entries", []), payload.get("warnings", [])


def prepare_duplicate_plan(
    entries: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
    skip_duplicate_indexes_raw: list[str],
) -> tuple[list[int], list[str], list[dict[str, Any]], int]:
    """
    Buat rencana penanganan duplikasi untuk branch confirm.

    Return:
      - selected_indexes: index duplikasi yang dipilih user untuk dikecualikan.
      - selected_indexes_payload: versi string untuk context/template.
      - deduped_entries: entries setelah duplikasi terpilih dihapus.
      - skipped_count: jumlah baris yang di-skip.
    """

    selected_indexes = parse_selected_duplicate_indexes(skip_duplicate_indexes_raw, duplicates)
    selected_indexes_payload = [str(i) for i in sorted(selected_indexes)]
    deduped_entries, skipped_count = filter_duplicate_entries(entries, duplicates, selected_indexes)
    return selected_indexes, selected_indexes_payload, deduped_entries, skipped_count


def persist_upload_entries(entries: list[dict[str, Any]]) -> None:
    """
    Persist valid entries ke storage utama kemudian perbarui ringkasan agregasi.
    Dipakai agar alur insert langsung maupun setelah dedupe memakai pola transaksi yang sama.
    """
    insert_entries(entries)
    refresh_aggregated_summary()


def build_upload_response(
    kind: Literal["render", "redirect"],
    flashes: list[tuple[str, str]],
    *,
    preview: dict[str, Any] | None = None,
    upload_preview_token: str | None = None,
    form_values: dict[str, Any] | None = None,
    pop_upload_session_token: bool = False,
) -> UploadFlowResponse:
    """Buat response upload terstruktur agar konsisten di seluruh branch alur."""
    return UploadFlowResponse(
        kind=kind,
        flashes=flashes,
        preview=preview,
        upload_preview_token=upload_preview_token,
        form_values=form_values,
        pop_upload_session_token=pop_upload_session_token,
    )


def handle_upload_confirm_with_duplicates(
    upload_folder: str,
    preview_token: str,
    file_path: str,
    preview_layout: str,
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
    if len(selected_indexes) < len(duplicates):
        preview_payload = to_preview_context(
            excel_preview_source_from_payload(
                file_name=token_payload.get("file_name", ""),
                payload=parse_payload,
                layout_override=preview_layout,
                upload_preview_token=preview_token,
                total_records=len(entries),
            ),
            duplicates=duplicates,
            skip_duplicate_indexes=selected_indexes_payload,
        )
        return build_upload_response(
            "render",
            [
                (
                    f"Hanya {len(selected_indexes)} dari {len(duplicates)} kandidat duplikasi yang dipilih. "
                    "Centang semua kandidat duplikasi yang ingin dikecualikan agar proses lanjut.",
                    "warning",
                )
            ],
            preview=preview_payload,
            upload_preview_token=preview_token,
            form_values=form_values,
        )

    metadata = token_payload.get("metadata", {})
    form_values = {
        "uploader": form_values.get("uploader", metadata.get("uploader", "")),
        "version": form_values.get("version", metadata.get("version", "")),
        "data_type": form_values.get("data_type", metadata.get("data_type", "")),
        "time_period": form_values.get("time_period", metadata.get("time_period", "")),
        "layout_override": preview_layout,
    }
    if not deduped_entries:
        preview_payload = to_preview_context(
            excel_preview_source_from_payload(
                file_name=token_payload.get("file_name", ""),
                payload=parse_payload,
                layout_override=preview_layout,
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
        persist_upload_entries(deduped_entries)
        delete_preview_session(upload_folder, preview_token)
        if os.path.exists(file_path):
            os.remove(file_path)
        if skipped_count > 0:
            msg = f"{len(deduped_entries)} baris disimpan, {skipped_count} baris duplikasi dikecualikan."
        else:
            msg = f"{len(deduped_entries)} baris data berhasil disimpan."
        return build_upload_response(
            "redirect",
            [(msg, "success")],
            pop_upload_session_token=True,
        )
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "UNIQUE constraint failed" in error_msg:
            flash_msg = (
                "Kombinasi pengunggah, versi, dan indikator ini sudah ada di basis data.\n"
                "Centang kandidat duplikasi yang ingin dikecualikan, lalu klik Konfirmasi & Simpan lagi."
            )
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
) -> UploadFlowResponse:
    try:
        persist_upload_entries(entries)
        delete_preview_session(upload_folder, preview_token)
        if os.path.exists(file_path):
            os.remove(file_path)
        return build_upload_response(
            "redirect",
            [(f"{len(entries)} baris data berhasil disimpan.", "success")],
            pop_upload_session_token=True,
        )
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "UNIQUE constraint failed" in error_msg:
            flash_msg = (
                "Kombinasi pengunggah, versi, dan indikator ini sudah ada di basis data.\n"
                "Silakan gunakan versi yang berbeda atau tandai semua kandidat duplikasi yang akan dikecualikan."
            )
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
        os.remove(destination)
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
    layout_override: str,
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
        layout_override=layout_override,
        payload=payload,
        entries=entries,
        duplicates=duplicates,
    )
    return build_upload_response(
        "render",
        [
            (
                f"Ditemukan {len(duplicates)} konflik duplikasi. "
                "Gunakan Konfirmasi pada pratinjau untuk memilih opsi lewati duplikasi.",
                "error",
            )
        ],
        preview=preview_payload,
        upload_preview_token=upload_token,
        form_values=form_values,
    )


def handle_upload_post_file_save_without_duplicates(
    entries: list[dict[str, Any]],
    form_values: dict[str, str],
) -> UploadFlowResponse:
    try:
        persist_upload_entries(entries)
        return build_upload_response(
            "redirect",
            [(f"{len(entries)} baris data berhasil disimpan.", "success")],
        )
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "UNIQUE constraint failed" in error_msg:
            flash_msg = (
                "Kombinasi pengunggah, versi, dan indikator ini sudah ada di basis data.\n"
                "Silakan gunakan versi yang berbeda atau tandai semua kandidat duplikasi yang akan dikecualikan."
            )
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
    layout_override: str,
    payload: dict[str, Any],
    entries: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
) -> UploadFlowResponse:
    metadata = {
        "uploader": form_values["uploader"],
        "version": form_values["version"],
        "data_type": form_values["data_type"],
        "time_period": form_values["time_period"],
    }
    upload_token = cache_upload_preview(
        upload_folder,
        destination,
        display_name,
        metadata,
        layout_override,
        payload,
        duplicates,
    )
    preview_payload = to_preview_context(
        excel_preview_source_from_payload(
            file_name=display_name,
            payload=payload,
            layout_override=layout_override,
            upload_preview_token=upload_token,
            total_records=len(entries),
        ),
        duplicates=duplicates,
        skip_duplicate_indexes=[str(i) for i in range(len(duplicates))],
    )
    if duplicates:
        info_flash = (f"Ditemukan {len(duplicates)} konflik duplikasi dengan data yang sudah ada.", "warning")
    else:
        info_flash = ("Klik tombol konfirmasi untuk menyimpan data yang sudah dipratinjau.", "info")
    return build_upload_response(
        "render",
        [info_flash],
        preview=preview_payload,
        upload_preview_token=upload_token,
        form_values=form_values,
    )


def process_upload_confirm(
    upload_folder: str,
    preview_token: str,
    form_values: dict[str, str],
    skip_duplicate_indexes_raw: list[str],
) -> UploadFlowResponse:
    """
    Handle POST action=confirm.

    Contract:
      Input:
        - upload_folder: direktori penyimpanan sesi file preview.
        - preview_token: token sesi preview yang dibuat saat `build_upload_preview`.
        - form_values: metadata formulir wajib (uploader/version/data_type/time_period/layout_override).
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
    preview_layout = token_payload.get("layout_override", "auto")
    try:
        payload, entries, _ = parse_and_validate_upload_payload(
            file_path,
            meta["uploader"],
            meta["version"],
            meta["data_type"],
            meta["time_period"],
            layout_override=preview_layout,
            preview_limit=0,
        )
    except Exception as e:
        return build_upload_response(
            "redirect",
            [(f"Gagal memproses berkas pratinjau: {str(e)}", "error")],
        )
    if not entries:
        return build_upload_response("redirect", [("Sesi pratinjau tidak memuat data valid.", "error")])

    duplicates = find_duplicate_entries_in_db(meta["uploader"], meta["version"], entries)
    if duplicates:
        return handle_upload_confirm_with_duplicates(
            upload_folder=upload_folder,
            preview_token=preview_token,
            file_path=file_path,
            preview_layout=preview_layout,
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
    )


def process_upload_post_file(
    upload_folder: str,
    destination: str,
    display_name: str,
    form_values: dict[str, str],
    action: str,
) -> UploadFlowResponse:
    """
    Setelah file multipart tersimpan: parse Excel lalu pilih alur preview / simpan.

    Contract:
      Input:
        - upload_folder: lokasi disk untuk sesi preview.
        - destination: path file yang baru disimpan.
        - display_name: nama file asli dari user.
        - form_values: metadata uploader/version/data_type/time_period.
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
    layout_override = form_values.get("layout_override", "auto") or "auto"

    try:
        payload, entries, warnings = parse_and_validate_upload_payload(
            destination,
            uploader,
            version,
            data_type,
            time_period,
            layout_override=layout_override or "auto",
        )
    except Exception as e:
        os.remove(destination)
        return build_upload_response(
            "render",
            [(f"Gagal membaca berkas Excel: {str(e)}", "error")],
            preview=None,
            upload_preview_token=None,
            form_values=form_values,
        )

    if not entries:
        return handle_upload_post_file_no_entries(destination, form_values, warnings)

    duplicates = find_duplicate_entries_in_db(uploader, version, entries)
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
                layout_override=layout_override,
                payload=payload,
                entries=entries,
                duplicates=duplicates,
                form_values=form_values,
            )

        try:
            response = handle_upload_post_file_save_without_duplicates(entries, form_values)
            if response.kind == "redirect":
                if os.path.exists(destination):
                    os.remove(destination)
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
        layout_override=layout_override,
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
) -> ManualFlowResponse:
    if not uploader or not version or not indicator or not value or not period_date:
        return ManualFlowResponse(
            kind="render",
            flashes=[("Semua kolom metadata dan data wajib diisi.", "error")],
        )
    validation_errors = validate_metadata(data_type, time_period)
    if validation_errors:
        return ManualFlowResponse(
            kind="render",
            flashes=[(e, "error") for e in validation_errors],
        )
    manual_entry = build_manual_entry(
        uploader, version, data_type, time_period, period_date, indicator, value
    )
    if manual_entry is None:
        return ManualFlowResponse(
            kind="render",
            flashes=[("Nilai indikator tidak valid.", "error")],
        )
    try:
        insert_entries([manual_entry])
        refresh_aggregated_summary()
        return ManualFlowResponse(
            kind="redirect",
            flashes=[("Entri manual berhasil dicatat dan disimpan.", "success")],
        )
    except sqlite3.IntegrityError as exc:
        flash_msg = (
            "Data duplikat: kombinasi pengunggah, versi, indikator, periode, dan waktu sudah ada.\n"
            if "UNIQUE constraint failed" in str(exc)
            else f"Terjadi kesalahan database: {exc}"
        )
        return ManualFlowResponse(kind="render", flashes=[(flash_msg, "error")])
