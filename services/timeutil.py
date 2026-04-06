# -*- coding: utf-8 -*-
"""Timezone-aware UTC helpers (replaces deprecated datetime.utcnow())."""
from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Naive UTC instant as ISO string, matching legacy utcnow().isoformat() shape for SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def utc_now_timestamp() -> float:
    """Unix timestamp (seconds) for the current UTC instant."""
    return datetime.now(timezone.utc).timestamp()
