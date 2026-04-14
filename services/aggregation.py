# -*- coding: utf-8 -*-
"""Build and cache landing-page aggregated summary (latest metadata + cards)."""
from __future__ import annotations

import json
import logging
import time
from typing import Dict

from models import (
    get_aggregated_cards,
    get_latest_metadata,
    load_cached_summary,
    save_aggregated_summary,
)

_log = logging.getLogger(__name__)


def refresh_aggregated_summary() -> Dict:
    t0 = time.perf_counter()
    _log.info("refresh_aggregated_summary_started")
    latest = get_latest_metadata()
    cards = get_aggregated_cards()
    summary = {"latest": latest, "cards": cards}
    save_aggregated_summary(summary)
    duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    try:
        approx_bytes = len(json.dumps(summary, default=str, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError):
        approx_bytes = None
    _log.info(
        "refresh_aggregated_summary_finished duration_ms=%s summary_json_bytes=%s",
        duration_ms,
        approx_bytes,
    )
    return summary


def fetch_aggregated_summary() -> Dict:
    cached = load_cached_summary()
    if cached:
        return cached
    return refresh_aggregated_summary()
