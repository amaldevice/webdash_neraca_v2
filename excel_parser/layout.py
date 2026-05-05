# -*- coding: utf-8 -*-
"""Template format detection and header-row / materialized DataFrame logic."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from excel_parser.constants import MAX_DETECTION_ROWS, MAX_LAYOUT_LOOKAHEAD_ROWS
from excel_parser.normalize import (
    _count_period_cells,
    _is_blank,
    _looks_like_period,
    _normalize_value,
    _row_non_empty_count,
)


def detect_template_format(df: pd.DataFrame) -> str:
    """Backward-compatible template detection for existing vertical/horizontal formats."""
    if df.empty:
        return "horizontal"  # Default for empty files
    first_col = df.iloc[:, 0].astype(str)
    if first_col.str.contains(r"\d{4}", na=False).any():
        return "vertical"
    return "horizontal"


def _detect_layout(
    df: pd.DataFrame,
    layout_override: str = "auto",
) -> tuple[str, int, list[str]]:
    warnings: list[str] = []
    row_limit = min(len(df), MAX_DETECTION_ROWS)

    def vertical_candidate(row_idx: int) -> bool:
        row = df.iloc[row_idx]
        if _row_non_empty_count(row) < 2:
            return False
        if _looks_like_period(_normalize_value(row.iloc[0])):
            return False
        if row_idx + 1 >= len(df):
            return False
        next_row = df.iloc[row_idx + 1]
        if not _looks_like_period(_normalize_value(next_row.iloc[0])):
            return False
        lookahead = df.iloc[row_idx + 1 : row_idx + 1 + MAX_LAYOUT_LOOKAHEAD_ROWS, 0]
        if lookahead.empty:
            return False
        ratio = _count_period_cells(lookahead) / max(1, len(lookahead))
        return ratio >= 0.40

    def horizontal_candidate(row_idx: int) -> bool:
        row = df.iloc[row_idx]
        if _row_non_empty_count(row.iloc[1:]) < 2:
            return False
        if _looks_like_period(_normalize_value(row.iloc[0])):
            return False
        ratio = _count_period_cells(row.iloc[1:]) / max(1, _row_non_empty_count(row.iloc[1:]))
        return ratio >= 0.40

    if layout_override in {"vertical", "horizontal"}:
        preferred = layout_override
        scan_range = range(row_limit)
        if preferred == "vertical":
            for row_idx in scan_range:
                if vertical_candidate(row_idx):
                    return preferred, row_idx, warnings
        else:
            for row_idx in scan_range:
                if horizontal_candidate(row_idx):
                    return preferred, row_idx, warnings
        warnings.append(
            f"Override '{preferred}' tidak ditemukan dengan jelas; akan fallback ke deteksi otomatis."
        )

    for row_idx in range(row_limit):
        row = df.iloc[row_idx]
        if _is_blank(row.iloc[0]) and _row_non_empty_count(row) == 0:
            continue
        if vertical_candidate(row_idx):
            return "vertical", row_idx, warnings
        if horizontal_candidate(row_idx):
            return "horizontal", row_idx, warnings

    warnings.append(
        "Tidak menemukan header yang jelas (kemungkinan ada banyak metadata); akan fallback ke format lama."
    )
    return "horizontal", 0, warnings


def _materialize_data_frame(
    df: pd.DataFrame,
    header_row_idx: int,
    _layout: str,
) -> Optional[pd.DataFrame]:
    data = df.iloc[header_row_idx + 1 :].copy()
    if data.empty:
        return None

    headers = df.iloc[header_row_idx].tolist()
    max_cols = min(len(headers), data.shape[1])
    if max_cols < 2:
        return None
    data = data.iloc[:, :max_cols].copy()
    data.columns = headers[:max_cols]
    return data
