# -*- coding: utf-8 -*-
"""POST action handlers for /data-management (CRUD + bulk); returns flash (message, category) tuples.

Transactional model is **mixed (campuran)**: each action runs as the caller's unit; underlying
writers in ``models/mutations`` use ``write_session`` per operation. See
``docs/codebase/data-management-actions.md`` for rationale (#83).
"""
from __future__ import annotations

from typing import Any, List, Tuple

from models import (
    bulk_delete_entries,
    bulk_update_entries,
    delete_data_by_filter,
    delete_data_entry,
    insert_single_entry,
    update_data_entry_full,
)

FlashTuple = Tuple[str, str]


def _norm_dataset_filter(raw: str | None) -> str | None:
    dc = (raw or "").strip()
    return None if dc == "" else dc


def apply_data_management_post(
    form: Any,
    *,
    data_type: str,
    time_period: str,
    uploader: str,
    indicator: str,
    period_start: str | None,
    period_end: str | None,
    value_min: float | None,
    value_max: float | None,
    dataset_code: str = "",
) -> List[FlashTuple]:
    """Run the requested action; side effects on DB. Caller applies flash() for each tuple."""
    messages: List[FlashTuple] = []
    action = form.get("action")

    if action == "delete_single":
        entry_id = form.get("entry_id")
        if entry_id:
            delete_data_entry(entry_id)
            messages.append(("Data berhasil dihapus.", "success"))

    elif action == "delete_by_filter":
        deleted_count = delete_data_by_filter(
            data_type=data_type or None,
            time_period=time_period or None,
            uploader=uploader or None,
            indicator=indicator or None,
            period_start=period_start,
            period_end=period_end,
            value_min=value_min,
            value_max=value_max,
            dataset_code=_norm_dataset_filter(dataset_code),
        )
        messages.append((f"{deleted_count} data berhasil dihapus berdasarkan filter.", "success"))

    elif action == "update":
        entry_id = form.get("entry_id")
        update_uploader = form.get("update_uploader", "").strip()
        update_version = form.get("update_version", "").strip()
        update_indicator = form.get("update_indicator", "").strip()
        update_value = form.get("update_value", "").strip()
        update_data_type = form.get("update_data_type", "").strip()
        update_time_period = form.get("update_time_period", "").strip()

        if entry_id and all([update_uploader, update_version, update_indicator, update_value]):
            try:
                update_data_entry_full(
                    entry_id,
                    {
                        "uploader_name": update_uploader,
                        "version": update_version,
                        "indicator_name": update_indicator,
                        "value": float(update_value),
                        "data_type": update_data_type,
                        "time_period": update_time_period,
                    },
                )
                messages.append(("Data berhasil diperbarui.", "success"))
            except ValueError:
                messages.append(("Nilai harus berupa angka.", "error"))
            except Exception as e:
                messages.append((f"Terjadi kesalahan saat memperbarui data: {str(e)}", "error"))

    elif action == "bulk_delete":
        selected_ids = form.getlist("selected_ids[]")
        if selected_ids:
            deleted_count = bulk_delete_entries(selected_ids)
            messages.append((f"{deleted_count} data berhasil dihapus.", "success"))
        else:
            messages.append(("Tidak ada data yang dipilih untuk dihapus.", "error"))

    elif action == "bulk_update":
        selected_ids = form.getlist("selected_ids[]")
        if not selected_ids:
            messages.append(("Tidak ada data yang dipilih untuk diperbarui.", "error"))
        else:
            updates = {}
            update_uploader = form.get("bulk_update_uploader", "").strip()
            update_version = form.get("bulk_update_version", "").strip()
            update_data_type = form.get("bulk_update_data_type", "").strip()
            update_time_period = form.get("bulk_update_time_period", "").strip()
            update_value = form.get("bulk_update_value", "").strip()

            if update_uploader:
                updates["uploader_name"] = update_uploader
            if update_version:
                updates["version"] = update_version
            if update_data_type:
                updates["data_type"] = update_data_type
            if update_time_period:
                updates["time_period"] = update_time_period
            if update_value:
                try:
                    updates["value"] = float(update_value)
                except ValueError:
                    messages.append(("Nilai harus berupa angka.", "error"))
                    return messages

            if updates:
                updated_count = bulk_update_entries(selected_ids, updates)
                messages.append((f"{updated_count} data berhasil diperbarui.", "success"))
            else:
                messages.append(("Tidak ada kolom yang diisi untuk diperbarui.", "error"))

    elif action == "insert":
        insert_uploader = form.get("insert_uploader", "").strip()
        insert_version = form.get("insert_version", "").strip()
        insert_data_type = form.get("insert_data_type", "").strip()
        insert_time_period = form.get("insert_time_period", "").strip()
        insert_period_date = form.get("insert_period_date", "").strip()
        insert_indicator = form.get("insert_indicator", "").strip()
        insert_value = form.get("insert_value", "").strip()
        insert_dataset_code = form.get("insert_dataset_code", "").strip()

        if all([insert_uploader, insert_version, insert_indicator, insert_value, insert_period_date]):
            try:
                insert_single_entry(
                    uploader=insert_uploader,
                    version=insert_version,
                    data_type=insert_data_type,
                    time_period=insert_time_period,
                    period_date=insert_period_date,
                    indicator=insert_indicator,
                    value=float(insert_value),
                    dataset_code=insert_dataset_code,
                )
                messages.append(("Data baru berhasil ditambahkan.", "success"))
            except ValueError:
                messages.append(("Nilai harus berupa angka.", "error"))
        else:
            messages.append(("Semua kolom wajib diisi.", "error"))

    return messages
