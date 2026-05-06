# -*- coding: utf-8 -*-
"""SQLite persistence split into connection, queries, mutations, and browse."""
from __future__ import annotations

from .browse import (
    get_filter_options,
)
from .connection import DB_PATH, init_db
from .mutations import (
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
from .queries import get_landing_summary

__all__ = [
    "DB_PATH",
    "bulk_delete_entries",
    "bulk_update_entries",
    "clear_all_data",
    "delete_data_by_filter",
    "delete_data_entry",
    "get_filter_options",
    "get_landing_summary",
    "get_total_entries_count",
    "init_db",
    "insert_entries",
    "upsert_entries",
    "insert_single_entry",
    "query_data_entries",
    "update_data_entry",
    "update_data_entry_full",
]
