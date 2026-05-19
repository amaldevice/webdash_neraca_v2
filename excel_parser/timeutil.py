# -*- coding: utf-8 -*-
"""UTC helpers for excel_parser — avoids dependency on services.timeutil."""
from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Naive UTC instant as ISO string, matching legacy utcnow().isoformat() shape for SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
