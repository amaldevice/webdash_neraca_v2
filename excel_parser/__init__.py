# -*- coding: utf-8 -*-
"""Excel ingestion: split into normalize, layout, records, parse_layouts, payload."""
from __future__ import annotations

from excel_parser.constants import MAX_DETECTION_ROWS, MAX_LAYOUT_LOOKAHEAD_ROWS, PREVIEW_SAMPLE_LIMIT
from excel_parser.layout import _detect_layout, _materialize_data_frame, detect_template_format
from excel_parser.normalize import (
    _count_period_cells,
    _is_blank,
    _looks_like_period,
    _normalize_value,
    _parse_period,
    _row_non_empty_count,
    _to_float,
    _trim_sparse_data,
)
from excel_parser.parse_layouts import _parse_horizontal_layout, _parse_vertical_layout
from excel_parser.payload import parse_excel, parse_excel_payload
from excel_parser.records import _normalize_record, _period_text

__all__ = [
    "MAX_DETECTION_ROWS",
    "MAX_LAYOUT_LOOKAHEAD_ROWS",
    "PREVIEW_SAMPLE_LIMIT",
    "_count_period_cells",
    "_detect_layout",
    "_is_blank",
    "_looks_like_period",
    "_materialize_data_frame",
    "_normalize_record",
    "_normalize_value",
    "_parse_horizontal_layout",
    "_parse_period",
    "_parse_vertical_layout",
    "_period_text",
    "_row_non_empty_count",
    "_to_float",
    "_trim_sparse_data",
    "detect_template_format",
    "parse_excel",
    "parse_excel_payload",
]
