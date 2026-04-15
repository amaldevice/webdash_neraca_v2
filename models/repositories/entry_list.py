# -*- coding: utf-8 -*-
"""Entry list reads for routes (no SQL here; delegates to ``models.queries``)."""
from __future__ import annotations

from typing import Any, Mapping

from models.queries import get_total_entries_count, query_data_entries


def fetch_entries_for_list(*, limit: int, offset: int, filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    return query_data_entries(limit=limit, offset=offset, **dict(filters))


def count_entries_for_list(filters: Mapping[str, Any]) -> int:
    return get_total_entries_count(**dict(filters))
