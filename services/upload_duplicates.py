# -*- coding: utf-8 -*-
"""
Duplicate-detection helpers extracted from upload_flow.

Pure functions that compute duplicate warnings, hydrate duplicate records,
and plan deduplication actions — no HTTP or database writes.
"""
from __future__ import annotations

from typing import Any

from services.upload_preview import filter_duplicate_entries, parse_selected_duplicate_indexes


def _duplicate_conflict_message() -> str:
    return (
        "Terdeteksi data duplikasi: kombinasi unik pengunggah, versi, indikator, dan periode "
        "sudah ada di basis data.\n"
        "Gunakan versi yang berbeda untuk menambahkan data baru, "
        "atau lanjutkan di pratinjau lalu tandai baris yang ingin dikecualikan agar tidak ditimpa."
    )


def _collect_internal_duplicate_counts(entries: list[dict[str, Any]]) -> dict[tuple[str, int, int | None, int | None], int]:
    """Hitung berapa kali setiap kombinasi indikator+periode muncul di dalam file upload."""
    if not entries:
        return {}
    counts: dict[tuple[str, int, int | None, int | None], int] = {}
    for entry in entries:
        indicator = (entry.get("indicator_name") or "").strip()
        year = entry.get("year")
        month = entry.get("month")
        quarter = entry.get("quarter")
        if not indicator or year is None:
            continue
        counts[(indicator, int(year), month, quarter)] = counts.get((indicator, int(year), month, quarter), 0) + 1
    return {key: count for key, count in counts.items() if count > 1}


def _build_internal_duplicate_warning_message(
    duplicate_counts: dict[tuple[str, int, int | None, int | None], int]
) -> str | None:
    if not duplicate_counts:
        return None
    duplicate_groups = len(duplicate_counts)
    duplicate_rows = sum(count - 1 for count in duplicate_counts.values())
    return (
        f"Ditemukan {duplicate_rows} baris duplikasi ekstra dalam satu file untuk "
        f"{duplicate_groups} kombinasi indikator + periode.\n"
        "Bersihkan baris duplikat pada file sebelum menyimpan, "
        "atau bagi ke file versi yang berbeda."
    )


def _hydrate_duplicate_records_with_values(
    duplicate_records: list[dict[str, Any]],
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Enrich duplicate candidates with uploaded values so UI can show nilai in preview rows.
    """
    value_by_key: dict[tuple, Any] = {}
    for entry in entries:
        key = (
            entry.get("indicator_name"),
            entry.get("year"),
            entry.get("month"),
            entry.get("quarter"),
            (entry.get("dataset_code") or entry.get("dataset_slug") or "").strip(),
        )
        if key not in value_by_key:
            value_by_key[key] = entry.get("value")
    hydrated: list[dict[str, Any]] = []
    for duplicate in duplicate_records:
        key = (
            duplicate.get("indicator_name"),
            duplicate.get("year"),
            duplicate.get("month"),
            duplicate.get("quarter"),
            (duplicate.get("dataset_code") or "").strip(),
        )
        hydrated.append({**duplicate, "value": value_by_key.get(key)})
    return hydrated


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


def _build_duplicate_confirmation_summary(
    duplicates: list[dict[str, Any]],
    selected_indexes: set[int],
    deduped_entries: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """
    Hitung ringkasan penanganan duplikasi saat confirm.

    Return:
      - skipped_count: jumlah kandidat duplikasi yang dikecualikan.
      - overwrite_count: jumlah kandidat duplikasi yang akan ditimpa.
      - safe_rows_count: jumlah baris non-duplikasi yang akan disimpan.
    """
    duplicate_keys = [
        (
            duplicate.get("indicator_name"),
            duplicate.get("year"),
            duplicate.get("month"),
            duplicate.get("quarter"),
            (duplicate.get("dataset_code") or "").strip(),
        )
        for duplicate in duplicates
    ]
    skipped_count = len(selected_indexes)
    overwrite_indexes = [i for i in range(len(duplicate_keys)) if i not in selected_indexes]
    overwrite_keys = {duplicate_keys[i] for i in overwrite_indexes if 0 <= i < len(duplicate_keys)}
    overwrite_count = len(overwrite_indexes)

    deduped_duplicate_count = 0
    for entry in deduped_entries:
        key = (
            entry.get("indicator_name"),
            entry.get("year"),
            entry.get("month"),
            entry.get("quarter"),
            (entry.get("dataset_code") or entry.get("dataset_slug") or "").strip(),
        )
        if key in overwrite_keys:
            deduped_duplicate_count += 1
    safe_rows_count = len(deduped_entries) - deduped_duplicate_count
    return skipped_count, overwrite_count, safe_rows_count
