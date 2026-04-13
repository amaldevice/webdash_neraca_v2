# -*- coding: utf-8 -*-
"""SQLite persistence: split into connection, queries, mutations, browse, summary_store."""
from __future__ import annotations

from services.period_comparisons import (
    calculate_current_to_current,
    calculate_monthly_comparison,
    calculate_period_comparisons,
    calculate_quarterly_comparison,
    calculate_ytd_comparison,
    calculate_yearly_comparison,
)

from .browse import (
    get_aggregated_cards,
    get_distinct_years,
    get_filter_options,
    get_latest_metadata,
    get_unique_indicators,
)
from .connection import DB_PATH, get_conn, init_db
from .data_filters import _build_data_entry_filter_clauses
from .mutations import (
    _to_float,
    bulk_delete_entries,
    bulk_update_entries,
    clear_all_data,
    delete_data_by_filter,
    delete_data_entry,
    insert_entries,
    insert_single_entry,
    upsert_entries,
    update_data_entry,
    update_data_entry_full,
)
from .queries import get_total_entries_count, query_data_entries
from .summary_store import load_cached_summary, save_aggregated_summary

__all__ = [
    "DB_PATH",
    "bulk_delete_entries",
    "bulk_update_entries",
    "calculate_current_to_current",
    "calculate_monthly_comparison",
    "calculate_period_comparisons",
    "calculate_quarterly_comparison",
    "calculate_ytd_comparison",
    "calculate_yearly_comparison",
    "clear_all_data",
    "delete_data_by_filter",
    "delete_data_entry",
    "get_aggregated_cards",
    "get_conn",
    "get_distinct_years",
    "get_filter_options",
    "get_latest_metadata",
    "get_total_entries_count",
    "get_unique_indicators",
    "init_db",
    "insert_entries",
    "upsert_entries",
    "insert_single_entry",
    "load_cached_summary",
    "query_data_entries",
    "save_aggregated_summary",
    "update_data_entry",
    "update_data_entry_full",
    "_build_data_entry_filter_clauses",
    "_to_float",
]
