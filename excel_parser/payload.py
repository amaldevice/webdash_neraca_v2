# -*- coding: utf-8 -*-
"""Orchestrate read_excel → layout → parse → preview payload."""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

from excel_parser.constants import PREVIEW_SAMPLE_LIMIT
from excel_parser.dataset_long import try_parse_dataset_long_dataframe
from excel_parser.layout import _detect_layout, _materialize_data_frame, detect_template_format
from excel_parser.normalize import _trim_sparse_data
from excel_parser.parse_layouts import _parse_horizontal_layout, _parse_vertical_layout
from excel_parser.records import _period_text
from services.dataset_catalog import dataset_sheet_read_candidates, get_dataset_or_none


def _resolve_read_sheet(
    file_path: str,
    sheet_name: str | int | None,
    definition,
) -> tuple[str | int | None, bool]:
    """
    Pick sheet to read.

    Returns ``(resolved, ok)``. ``ok`` is False when a dataset slug was given but no sheet matched.
    """
    with pd.ExcelFile(file_path, engine="openpyxl") as xl:
        names = xl.sheet_names
    name_set = set(names)

    resolved: str | int | None = None
    if sheet_name is not None and sheet_name != "":
        if isinstance(sheet_name, int):
            if 0 <= sheet_name < len(names):
                resolved = sheet_name
        elif str(sheet_name) in name_set:
            resolved = str(sheet_name)

    if resolved is None and definition is not None:
        for cand in dataset_sheet_read_candidates(definition):
            if cand in name_set:
                resolved = cand
                break

    if definition is not None and resolved is None:
        return None, False

    return resolved, True


def parse_excel_payload(
    file_path: str,
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    *,
    layout_override: str = "auto",
    preview_limit: int = PREVIEW_SAMPLE_LIMIT,
    sheet_name: str | int | None = None,
    dataset_slug: str | None = None,
    require_dataset_context: bool = False,
) -> Dict[str, object]:
    """Parse excel and return entries + metadata for preview and validation.

    ``sheet_name``: lembar yang dibaca (default: lembar pertama). ``dataset_slug`` dicatat di payload untuk audit;
    mode ketat ``require_dataset_context`` menolak parse bila slug kosong (uji / gate produksi).
    """
    payload: Dict[str, object] = {
        "entries": [],
        "layout": "horizontal",
        "header_row": 0,
        "source_rows": 0,
        "source_columns": 0,
        "warnings": [],
        "invalid_rows": [],
        "sample": [],
        "source_mode": "headered",
        "dataset_slug": (dataset_slug or "").strip(),
        "sheet_name": "",
    }
    warnings: List[str] = []

    if require_dataset_context and not (dataset_slug or "").strip():
        warnings.append("dataset_slug wajib diisi untuk konteks parse (mode ketat).")
        payload["warnings"] = warnings
        return payload

    slug = (dataset_slug or "").strip()
    definition = get_dataset_or_none(slug) if slug else None

    resolved, sheet_ok = _resolve_read_sheet(file_path, sheet_name, definition)
    if not sheet_ok:
        with pd.ExcelFile(file_path, engine="openpyxl") as xl:
            sheet_names = xl.sheet_names
        warnings.append(
            "Lembar data dataset tidak ditemukan di berkas. "
            f"Lembar tersedia (awal): {', '.join(sheet_names[:12])}"
            + (" …" if len(sheet_names) > 12 else "")
        )
        payload["warnings"] = warnings
        return payload

    if definition is not None and resolved is not None:
        try:
            df_header = pd.read_excel(
                file_path,
                sheet_name=resolved,
                header=0,
                engine="openpyxl",
            )
        except ValueError:
            df_header = pd.DataFrame()
        # Do not `_trim_sparse_data` here: it can drop trailing numeric columns (e.g. `nilai`)
        # that are still sparse in sample rows but required by the long-format contract.
        long_entries = try_parse_dataset_long_dataframe(
            df_header,
            definition,
            uploader=uploader,
            version=version,
            data_type=data_type,
        )
        if long_entries is not None:
            payload["entries"] = long_entries
            payload["sheet_name"] = str(resolved)
            payload["source_rows"] = int(df_header.shape[0])
            payload["source_columns"] = int(df_header.shape[1])
            payload["layout"] = "long"
            payload["source_mode"] = "long"
            payload["invalid_rows"] = []
            payload["warnings"] = warnings
            payload["header_row"] = 0
            payload["sample"] = [
                {
                    "indicator_name": entry["indicator_name"],
                    "value": entry["value"],
                    "time_period": _period_text(entry),
                }
                for entry in long_entries[:preview_limit]
            ]
            return payload

    read_kw: dict[str, object] = {"engine": "openpyxl", "header": None}
    if resolved is not None:
        read_kw["sheet_name"] = resolved
    payload["sheet_name"] = str(read_kw.get("sheet_name", "") or "")

    raw_df = _trim_sparse_data(pd.read_excel(file_path, **read_kw))
    if raw_df.empty:
        warnings.append("File Excel kosong.")
        payload["warnings"] = warnings
        return payload

    payload["source_rows"] = int(raw_df.shape[0])
    payload["source_columns"] = int(raw_df.shape[1])

    layout, header_row, detection_warnings = _detect_layout(
        raw_df,
        layout_override=layout_override.lower().strip() if layout_override else "auto",
    )
    warnings.extend(detection_warnings)
    payload["layout"] = layout
    payload["header_row"] = header_row

    parse_kwargs = {
        "uploader": uploader,
        "version": version,
        "layout": layout,
        "data_type": data_type,
        "time_period": time_period,
    }
    diagnostics: Dict[str, List[int]] = {"invalid_rows": []}
    entries: List[Dict] = []
    parsed_df = _materialize_data_frame(raw_df, header_row, layout)

    if parsed_df is None:
        warnings.append(
            "Gagal menentukan struktur data secara konsisten pada baris setelah header; fallback ke format lama."
        )
        fb_kw: dict[str, object] = {"engine": "openpyxl"}
        if resolved is not None:
            fb_kw["sheet_name"] = resolved
        fallback_df = pd.read_excel(file_path, **fb_kw)
        if fallback_df.empty:
            warnings.append("File Excel kosong setelah fallback.")
            payload["warnings"] = warnings
            return payload
        layout = detect_template_format(fallback_df)
        payload["layout"] = layout
        payload["source_mode"] = "legacy"
        if layout == "vertical":
            entries = _parse_vertical_layout(fallback_df, diagnostics=diagnostics, **parse_kwargs)
        else:
            entries = _parse_horizontal_layout(fallback_df, diagnostics=diagnostics, **parse_kwargs)
    else:
        if layout == "vertical":
            entries = _parse_vertical_layout(parsed_df, diagnostics=diagnostics, **parse_kwargs)
        else:
            entries = _parse_horizontal_layout(parsed_df, diagnostics=diagnostics, **parse_kwargs)

    payload["entries"] = entries
    payload["layout"] = layout
    payload["invalid_rows"] = diagnostics["invalid_rows"]
    payload["warnings"] = warnings
    payload["sample"] = [
        {
            "indicator_name": entry["indicator_name"],
            "value": entry["value"],
            "time_period": _period_text(entry),
        }
        for entry in entries[:preview_limit]
    ]
    return payload


def parse_excel(
    file_path: str,
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    *,
    layout_override: str = "auto",
    sheet_name: str | int | None = None,
    dataset_slug: str | None = None,
    require_dataset_context: bool = False,
) -> List[Dict]:
    payload = parse_excel_payload(
        file_path,
        uploader,
        version,
        data_type,
        time_period,
        layout_override=layout_override,
        preview_limit=0,
        sheet_name=sheet_name,
        dataset_slug=dataset_slug,
        require_dataset_context=require_dataset_context,
    )
    return payload["entries"]
