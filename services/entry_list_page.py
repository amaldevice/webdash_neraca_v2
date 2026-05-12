# -*- coding: utf-8 -*-
"""Single place for entry-list request parsing + paginated list bundle (preview, data-management, export cap)."""
from __future__ import annotations

from typing import Any, Literal, Mapping

from models.repositories.entry_list import count_entries_for_list, fetch_entries_for_list
from services.list_view import (
    EntryListParams,
    build_entries_filters_ui_dict,
    parse_entries_pagination,
)
from services.request_params import (
    data_entries_period_marker_range_from_request,
    get_value_range_params,
)

# Max rows returned by /export (must stay aligned with product expectation for large exports).
EXPORT_ENTRY_HARD_CAP = 1000


def _filter_map(request: Any, *, filter_source: Literal["args", "values"]) -> Mapping[str, Any]:
    return request.args if filter_source == "args" else request.values


def parse_entry_list_params_from_request(
    request: Any,
    *,
    filter_source: Literal["args", "values"],
) -> EntryListParams:
    src = _filter_map(request, filter_source=filter_source)
    data_type = src.get("data_type", "") or ""
    time_period = src.get("time_period", "") or ""
    uploader = src.get("uploader", "") or ""
    indicator = src.get("indicator", "") or ""
    dataset_code = src.get("dataset_code", "") or ""
    period_start, period_end = data_entries_period_marker_range_from_request(
        request, filter_source=filter_source
    )
    value_min, value_max = get_value_range_params(src)
    return EntryListParams.from_request_strings(
        data_type=data_type,
        time_period=time_period,
        uploader=uploader,
        indicator=indicator,
        period_start=period_start,
        period_end=period_end,
        value_min=value_min,
        value_max=value_max,
        dataset_code=dataset_code,
    )


def parse_entry_list_params_and_pagination(
    request: Any,
    *,
    filter_source: Literal["args", "values"],
) -> tuple[EntryListParams, int, int, int]:
    """Filters from ``request.args`` or ``request.values`` + ``page``/``limit`` from ``request.args``."""
    list_params = parse_entry_list_params_from_request(request, filter_source=filter_source)
    page, limit, offset = parse_entries_pagination(request)
    return list_params, page, limit, offset


def build_entry_list_page_bundle(
    list_params: EntryListParams,
    page: int,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch page of entries + UI filter dict (shared preview + data-management)."""
    qkw = list_params.to_query_kwargs()
    entries = fetch_entries_for_list(limit=limit, offset=offset, filters=qkw)
    total_entries = count_entries_for_list(qkw)
    filters = build_entries_filters_ui_dict(
        **list_params.to_ui_strings(),
        page=page,
        limit=limit,
        total_entries=total_entries,
    )
    return entries, filters


def fetch_entries_for_export(request: Any) -> list[dict[str, Any]]:
    """Same filters as preview; fixed cap for raw export download."""
    list_params = parse_entry_list_params_from_request(request, filter_source="args")
    return fetch_entries_for_list(
        limit=EXPORT_ENTRY_HARD_CAP,
        offset=0,
        filters=list_params.to_query_kwargs(),
    )
