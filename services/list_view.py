# -*- coding: utf-8 -*-
"""Shared pagination and filter wiring for preview-data and data-management list views."""
from __future__ import annotations

from typing import Any, Mapping, Optional

ALLOWED_ENTRY_PAGE_LIMITS = frozenset({5, 10, 15, 20, 30, 50, 100})


def normalize_entries_page_limit(limit_value: Any, default: int = 20) -> int:
    try:
        lim = int(limit_value)
    except (TypeError, ValueError):
        return default
    return lim if lim in ALLOWED_ENTRY_PAGE_LIMITS else default


def parse_entries_pagination(request: Any) -> tuple[int, int, int]:
    """Return (page, limit, offset) from Flask request.args."""
    try:
        page = int(request.args.get("page", 1) or 1)
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1
    limit = normalize_entries_page_limit(request.args.get("limit", 20), 20)
    offset = (page - 1) * limit
    return page, limit, offset


def entries_query_kwargs(
    data_type: Optional[str],
    time_period: Optional[str],
    uploader: Optional[str],
    indicator: Optional[str],
    period_start: Optional[str],
    period_end: Optional[str],
) -> dict[str, Any]:
    """Keyword args for query_data_entries / get_total_entries_count."""
    return {
        "data_type": data_type or None,
        "time_period": time_period or None,
        "uploader": uploader or None,
        "indicator": indicator or None,
        "period_start": period_start,
        "period_end": period_end,
    }


def build_entries_filters_ui_dict(
    *,
    data_type: str,
    time_period: str,
    uploader: str,
    indicator: str,
    period_start: str | None,
    period_end: str | None,
    page: int,
    limit: int,
    total_entries: int,
) -> Mapping[str, Any]:
    total_pages = (total_entries + limit - 1) // limit if limit else 0
    return {
        "data_type": data_type,
        "time_period": time_period,
        "uploader": uploader,
        "indicator": indicator,
        "start_period": period_start,
        "end_period": period_end,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_entries": total_entries,
    }
