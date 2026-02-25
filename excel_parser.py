from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd


def detect_template_format(df: pd.DataFrame) -> str:
    first_col = df.iloc[:, 0].astype(str)
    if first_col.str.contains(r"\d{4}", na=False).any():
        return "vertical"
    return "horizontal"


def _to_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_period(period_value) -> Dict[str, Optional[int]]:
    try:
        parsed = pd.to_datetime(period_value, errors="coerce")
        if pd.isna(parsed):
            return {"year": None, "month": None, "quarter": None}
        return {"year": parsed.year, "month": parsed.month, "quarter": parsed.quarter}
    except Exception:
        return {"year": None, "month": None, "quarter": None}


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
    df: pd.DataFrame, **kwargs
) -> List[Dict]:
    entries: List[Dict] = []
    seen_indicators = set()  # Track indicators per period to prevent duplicates

    for _, row in df.iterrows():
        period_value = row.iloc[0]
        period_indicators = set()  # Reset for each period

        for indicator, value in row.iloc[1:].items():
            # Skip if this indicator already processed for this period
            if indicator in period_indicators:
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

    return entries


def _parse_horizontal_layout(
    df: pd.DataFrame, **kwargs
) -> List[Dict]:
    entries: List[Dict] = []
    headers = df.columns[1:]
    for _, row in df.iterrows():
        indicator = row.iloc[0]
        for period_value, value in zip(headers, row.iloc[1:]):
            record = _normalize_record(
                indicator=indicator,
                value=value,
                period_value=period_value,
                **kwargs,
            )
            if record:
                entries.append(record)
    return entries


def parse_excel(
    file_path: str,
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
) -> List[Dict]:
    df = pd.read_excel(file_path, engine="openpyxl")
    layout = detect_template_format(df)
    kwargs = {
        "uploader": uploader,
        "version": version,
        "layout": layout,
        "data_type": data_type,
        "time_period": time_period,
    }
    if layout == "vertical":
        return _parse_vertical_layout(df, **kwargs)
    return _parse_horizontal_layout(df, **kwargs)
