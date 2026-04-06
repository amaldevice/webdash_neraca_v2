# -*- coding: utf-8 -*-
from __future__ import annotations

from config import ALLOWED_DATA_TYPES, ALLOWED_EXTENSIONS, ALLOWED_TIME_PERIODS


def allowed_file(filename: str) -> bool:
    """Validate file extensions for Excel uploads."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_metadata(data_type: str, time_period: str) -> list[str]:
    errors: list[str] = []
    if data_type.lower() not in ALLOWED_DATA_TYPES:
        errors.append("Tipe data tidak valid.")
    if time_period.lower() not in ALLOWED_TIME_PERIODS:
        errors.append("Periode tidak valid.")
    return errors
