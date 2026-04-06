# -*- coding: utf-8 -*-
"""Orchestrate read_excel → layout → parse → preview payload."""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

from excel_parser.constants import PREVIEW_SAMPLE_LIMIT
from excel_parser.layout import _detect_layout, _materialize_data_frame, detect_template_format
from excel_parser.normalize import _trim_sparse_data
from excel_parser.parse_layouts import _parse_horizontal_layout, _parse_vertical_layout
from excel_parser.records import _period_text


def parse_excel_payload(
    file_path: str,
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    *,
    layout_override: str = "auto",
    preview_limit: int = PREVIEW_SAMPLE_LIMIT,
) -> Dict[str, object]:
    """Parse excel and return entries + metadata for preview and validation."""
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
    }
    warnings: List[str] = []

    raw_df = _trim_sparse_data(pd.read_excel(file_path, engine="openpyxl", header=None))
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
        fallback_df = pd.read_excel(file_path, engine="openpyxl")
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
) -> List[Dict]:
    payload = parse_excel_payload(
        file_path,
        uploader,
        version,
        data_type,
        time_period,
        layout_override=layout_override,
        preview_limit=0,
    )
    return payload["entries"]
