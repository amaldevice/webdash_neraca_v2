# -*- coding: utf-8 -*-
"""
Stable public surface for ``excel_parser`` (no leading-underscore names).

Callers outside this package should import from ``excel_parser`` (re-exported here)
or ``excel_parser.api`` — not from ``excel_parser.normalize`` etc., unless extending internals.
"""
from __future__ import annotations

from excel_parser.constants import (
    MAX_DETECTION_ROWS,
    MAX_LAYOUT_LOOKAHEAD_ROWS,
    PREVIEW_SAMPLE_LIMIT,
)
from excel_parser.layout import (
    _detect_layout as detect_layout,
    _materialize_data_frame as materialize_data_frame,
    detect_template_format,
)
from excel_parser.normalize import (
    _count_period_cells as count_period_cells,
    _is_blank as is_blank,
    _looks_like_period as looks_like_period,
    _normalize_value as normalize_value,
    _parse_period as parse_period,
    _row_non_empty_count as row_non_empty_count,
    _to_float as to_float,
    _trim_sparse_data as trim_sparse_data,
)
from excel_parser.parse_layouts import (
    _parse_horizontal_layout as parse_horizontal_layout,
    _parse_vertical_layout as parse_vertical_layout,
)
from excel_parser.payload import parse_excel, parse_excel_payload
from excel_parser.records import _normalize_record as normalize_record, _period_text as period_text

__all__ = [
    "MAX_DETECTION_ROWS",
    "MAX_LAYOUT_LOOKAHEAD_ROWS",
    "PREVIEW_SAMPLE_LIMIT",
    "count_period_cells",
    "detect_layout",
    "detect_template_format",
    "is_blank",
    "looks_like_period",
    "materialize_data_frame",
    "normalize_record",
    "normalize_value",
    "parse_excel",
    "parse_excel_payload",
    "parse_horizontal_layout",
    "parse_period",
    "parse_vertical_layout",
    "period_text",
    "row_non_empty_count",
    "to_float",
    "trim_sparse_data",
]
