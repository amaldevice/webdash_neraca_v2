import re
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

MAX_DETECTION_ROWS = 30
MAX_LAYOUT_LOOKAHEAD_ROWS = 12
PREVIEW_SAMPLE_LIMIT = 10


def detect_template_format(df: pd.DataFrame) -> str:
    """Backward-compatible template detection for existing vertical/horizontal formats."""
    if df.empty:
        return "horizontal"  # Default for empty files
    first_col = df.iloc[:, 0].astype(str)
    if first_col.str.contains(r"\d{4}", na=False).any():
        return "vertical"
    return "horizontal"


def _to_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip().replace("\u00a0", "").replace(" ", "")
            normalized = re.sub(r"[^0-9+\-.,]", "", normalized)
            if not normalized:
                return None

            if "," in normalized and "." in normalized:
                last_dot = normalized.rfind(".")
                last_comma = normalized.rfind(",")
                if last_comma > last_dot:
                    # Format with thousands separator dot and decimal comma, e.g. 1.234,56
                    normalized = normalized.replace(".", "").replace(",", ".")
                else:
                    # Format with thousands separator comma and decimal dot, e.g. 1,234.56
                    normalized = normalized.replace(",", "")
            elif "," in normalized:
                # Indonesian-style decimal comma, e.g. 12,34
                normalized = normalized.replace(".", "").replace(",", ".")

            return float(normalized)
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _is_blank(value) -> bool:
    text = _normalize_value(value)
    return text == ""


def _parse_period(period_value) -> Dict[str, Optional[int]]:
    """Parse a period value into year/month/quarter tuple."""
    try:
        parsed = pd.to_datetime(period_value, errors="coerce")
        if pd.isna(parsed):
            return {"year": None, "month": None, "quarter": None}
        return {"year": parsed.year, "month": parsed.month, "quarter": parsed.quarter}
    except Exception:
        return {"year": None, "month": None, "quarter": None}


def _looks_like_period(value) -> bool:
    return _parse_period(value)["year"] is not None


def _trim_sparse_data(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully empty rows/columns to reduce noise from metadata-only cells."""
    if df.empty:
        return df
    trimmed = df.dropna(how="all")
    if trimmed.empty:
        return trimmed
    trimmed = trimmed.loc[:, trimmed.notna().any(axis=0)]
    return trimmed


def _count_period_cells(values) -> int:
    return sum(1 for value in values if _looks_like_period(value))


def _row_non_empty_count(row) -> int:
    return sum(1 for value in row if not _is_blank(value))


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
        # Header langsung sebelum data vertical biasanya diikuti periode/date di baris berikutnya.
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

    # Auto detection: prioritize candidate with highest confidence.
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
    layout: str,
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


def _period_text(entry: dict) -> str:
    year = entry.get("year")
    month = entry.get("month")
    quarter = entry.get("quarter")
    if year is None:
        return "-"
    if month:
        return f"{int(year)}-{int(month):02d}"
    if quarter:
        return f"{int(year)}-Q{int(quarter)}"
    return str(year)


def _normalize_record(
    *,
    uploader: str,
    version: str,
    layout: str,
    data_type: str,
    time_period: str,
    indicator: str,
    value,
    period_value,
) -> Optional[Dict]:
    parsed_value = _to_float(value)
    if parsed_value is None or not indicator:
        return None
    parsed_period = _parse_period(period_value)
    return {
        "uploader_name": uploader,
        "version": version,
        "template_type": layout,
        "data_type": data_type.lower().strip(),
        "time_period": time_period.lower().strip(),
        "indicator_name": str(indicator).strip(),
        "value": parsed_value,
        "unit": None,
        "region_code": None,
        "year": parsed_period["year"],
        "month": parsed_period["month"],
        "quarter": parsed_period["quarter"],
        "created_at": datetime.utcnow().isoformat(),
    }


def _parse_vertical_layout(
    df: pd.DataFrame,
    *,
    diagnostics: Optional[Dict[str, List[int]]] = None,
    **kwargs,
) -> List[Dict]:
    entries: List[Dict] = []
    invalid_rows: set[int] = set()

    for _, row in df.iterrows():
        period_value = row.iloc[0]
        period_row_display = int(row.name) + 1
        if _is_blank(period_value):
            invalid_rows.add(period_row_display)
            continue
        period_indicators = set()  # Reset for each period

        for indicator, value in row.iloc[1:].items():
            # Skip if this indicator already processed for this period
            if indicator in period_indicators:
                continue
            if _is_blank(indicator):
                continue

            record = _normalize_record(
                indicator=indicator,
                value=value,
                period_value=period_value,
                **kwargs,
            )
            if record:
                entries.append(record)
                period_indicators.add(indicator)
            else:
                invalid_rows.add(period_row_display)

    if diagnostics is not None:
        diagnostics["invalid_rows"] = sorted(invalid_rows)

    return entries


def _parse_horizontal_layout(
    df: pd.DataFrame,
    *,
    diagnostics: Optional[Dict[str, List[int]]] = None,
    **kwargs,
) -> List[Dict]:
    entries: List[Dict] = []
    headers = df.columns[1:]
    invalid_rows: set[int] = set()
    for _, row in df.iterrows():
        indicator = row.iloc[0]
        indicator_row_display = int(row.name) + 1
        if _is_blank(indicator):
            invalid_rows.add(indicator_row_display)
            continue
        for period_value, value in zip(headers, row.iloc[1:]):
            record = _normalize_record(
                indicator=indicator,
                value=value,
                period_value=period_value,
                **kwargs,
            )
            if record:
                entries.append(record)
            else:
                invalid_rows.add(indicator_row_display)

    if diagnostics is not None:
        diagnostics["invalid_rows"] = sorted(invalid_rows)

    return entries


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
