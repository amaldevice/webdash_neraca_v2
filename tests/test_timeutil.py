# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

from services.timeutil import utc_now_iso, utc_now_timestamp


def test_utc_now_iso_matches_legacy_shape():
    s = utc_now_iso()
    assert "T" in s and "+" not in s
    parsed = datetime.fromisoformat(s)
    assert parsed.tzinfo is None


def test_utc_now_timestamp_is_positive():
    assert utc_now_timestamp() > 1e9
