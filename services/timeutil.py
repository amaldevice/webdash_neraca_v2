# -*- coding: utf-8 -*-
"""Timezone-aware UTC helpers (replaces deprecated datetime.utcnow())."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta


_WITA_OFFSET = timedelta(hours=8)


def to_wita_iso(iso_dt: str | None) -> str:
    """Convert ISO-like datetime string (UTC or naive) to WITA display format."""
    if not iso_dt or not isinstance(iso_dt, str):
        return ""
    text = iso_dt.strip()
    if not text:
        return ""
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return iso_dt
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    dt = dt + _WITA_OFFSET
    return dt.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S WITA")


def wita_now_iso() -> str:
    """Naive local-time WITA instant as ISO-like string."""
    return (datetime.now(timezone.utc) + _WITA_OFFSET).replace(tzinfo=None).replace(
        microsecond=0
    ).isoformat(sep=" ", timespec="seconds")


def utc_now_iso() -> str:
    """Naive UTC instant as ISO string, matching legacy utcnow().isoformat() shape for SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def utc_now_timestamp() -> float:
    """Unix timestamp (seconds) for the current UTC instant."""
    return datetime.now(timezone.utc).timestamp()
