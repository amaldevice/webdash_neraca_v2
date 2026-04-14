# -*- coding: utf-8 -*-
"""Structured audit lines (no secrets); optional ``request_id`` from Flask ``g``."""
from __future__ import annotations

import json
import logging
from typing import Any

_audit = logging.getLogger("audit")


def _request_id() -> str | None:
    try:
        from flask import g

        rid = getattr(g, "request_id", None)
        return str(rid) if rid else None
    except RuntimeError:
        return None


def log_audit(event: str, **fields: Any) -> None:
    """
    Emit one INFO line: event + JSON object (stable keys for log processors).

    Omit None values; never pass raw tokens or CSRF values.
    """
    payload: dict[str, Any] = {"event": event}
    for key, value in fields.items():
        if value is None:
            continue
        payload[key] = value
    rid = _request_id()
    if rid:
        payload["request_id"] = rid
    _audit.info("%s %s", event, json.dumps(payload, default=str, ensure_ascii=False))
