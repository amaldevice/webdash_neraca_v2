# -*- coding: utf-8 -*-
"""Long-format REKAP rows (header row + typed columns) → data_entries-shaped dicts."""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import pandas as pd

from excel_parser.normalize import _to_float, parse_flexible_universal_period
from services.timeutil import utc_now_iso

if TYPE_CHECKING:
    from services.dataset_catalog import DatasetDefinition

_PERIOD_KEYS = frozenset({"tahun", "bulan", "triwulan", "nilai"})


def _norm_col(name: object) -> str:
    return str(name).strip()


def _row_dict(series: pd.Series, col_map: dict[str, str]) -> dict[str, object]:
    """Map normalized column key → cell value (original header preserved via col_map)."""
    out: dict[str, object] = {}
    for norm, original in col_map.items():
        if original in series.index:
            out[norm] = series[original]
    return out


def _build_indicator_from_row(definition: DatasetDefinition, row: dict[str, object]) -> str:
    parts: list[str] = []
    for h in definition.required_template_headers:
        if h.lower() in _PERIOD_KEYS:
            continue
        v = row.get(h.lower())
        if v is None or (isinstance(v, float) and pd.isna(v)):
            parts.append("")
        else:
            parts.append(str(v).strip())
    joined = " | ".join(parts)
    return joined if joined.strip() else definition.slug


def _coerce_int(val: object) -> Optional[int]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, int) and not isinstance(val, bool):
        return int(val)
    try:
        return int(float(str(val).strip()))
    except (TypeError, ValueError):
        return None


def try_parse_dataset_long_dataframe(
    df: pd.DataFrame,
    definition: DatasetDefinition,
    *,
    uploader: str,
    version: str,
    data_type: str,
) -> Optional[List[dict]]:
    """
    If ``df`` has all required template columns (case-insensitive), return parsed entries.

    Returns ``None`` if headers do not match long-format contract (caller falls back to wide parser).
    """
    if df is None or df.empty:
        return None

    raw_cols = [_norm_col(c) for c in df.columns]
    if len(set(raw_cols)) != len(raw_cols):
        return None

    col_map: dict[str, str] = {}
    for orig in df.columns:
        key = _norm_col(orig).lower()
        col_map[key] = str(orig)

    required_lower = {h.lower() for h in definition.required_template_headers}
    present_lower = set(col_map.keys())
    if not required_lower.issubset(present_lower):
        return None

    mode = definition.time_period_mode
    entries: List[dict] = []
    for idx, series in df.iterrows():
        row = _row_dict(series, col_map)
        nilai = _to_float(row.get("nilai"))
        if nilai is None:
            continue
        year = _coerce_int(row.get("tahun"))
        if year is None:
            continue
        month: Optional[int] = None
        quarter: Optional[int] = None
        if mode == "monthly":
            month = _coerce_int(row.get("bulan"))
            if month is None:
                continue
        elif mode == "quarterly":
            quarter = _coerce_int(row.get("triwulan"))
            if quarter is None:
                continue
        elif mode == "yearly":
            month = None
            quarter = None
        indicator_name = _build_indicator_from_row(definition, row)
        entries.append(
            {
                "uploader_name": uploader,
                "version": version,
                "template_type": "long",
                "data_type": data_type.lower().strip(),
                "time_period": definition.time_period_mode,
                "indicator_name": indicator_name,
                "value": float(nilai),
                "unit": None,
                "region_code": None,
                "year": year,
                "month": month,
                "quarter": quarter,
                "created_at": utc_now_iso(),
            }
        )
    return entries


def try_parse_universal_long_dataframe(
    df: pd.DataFrame,
    definition: DatasetDefinition,
    *,
    uploader: str,
    version: str,
    data_type: str,
    form_time_period: str,
) -> Optional[List[dict]]:
    """
    Long-format universal sheet (nama_dataset, indikator, periode, nilai) → entries.

    Returns ``None`` if headers do not match or definition is not universal_long.
    """
    if definition.template_mode != "universal_long":
        return None
    if df is None or df.empty:
        return None

    raw_cols = [_norm_col(c) for c in df.columns]
    if len(set(raw_cols)) != len(raw_cols):
        return None

    col_map: dict[str, str] = {}
    for orig in df.columns:
        key = _norm_col(orig).lower()
        col_map[key] = str(orig)

    required_lower = {h.lower() for h in definition.required_template_headers}
    present_lower = set(col_map.keys())
    if not required_lower.issubset(present_lower):
        return None

    tp_meta = (form_time_period or "monthly").strip().lower()
    if tp_meta not in {"monthly", "quarterly", "yearly"}:
        tp_meta = "monthly"

    entries: List[dict] = []
    for _idx, series in df.iterrows():
        row = _row_dict(series, col_map)
        nama_ds = _normalize_cell_text(row.get("nama_dataset"))
        indikator = _normalize_cell_text(row.get("indikator"))
        if not nama_ds or not indikator:
            continue
        nilai = _to_float(row.get("nilai"))
        if nilai is None:
            continue
        parsed = parse_flexible_universal_period(row.get("periode"))
        year = parsed.get("year")
        if year is None:
            continue
        month = parsed.get("month")
        quarter = parsed.get("quarter")
        indicator_name = f"{nama_ds} | {indikator}"
        entries.append(
            {
                "uploader_name": uploader,
                "version": version,
                "template_type": "universal_long",
                "data_type": data_type.lower().strip(),
                "time_period": tp_meta,
                "indicator_name": indicator_name,
                "value": float(nilai),
                "unit": None,
                "region_code": None,
                "year": int(year),
                "month": int(month) if month is not None else None,
                "quarter": int(quarter) if quarter is not None else None,
                "created_at": utc_now_iso(),
                "dataset_slug": "universal",
                "dataset_code": "universal",
            }
        )
    return entries


def _normalize_cell_text(val: object) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()
