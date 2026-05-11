# -*- coding: utf-8 -*-
"""Thin persistence seam for upload flows (insert vs upsert)."""
from __future__ import annotations

from typing import Any, Literal

from models import insert_entries, upsert_entries

_PersistMode = Literal["insert", "upsert"]


def _persist_entries(entries: list[dict[str, Any]], mode: _PersistMode) -> None:
    if mode == "insert":
        insert_entries(entries)
    else:
        upsert_entries(entries)


def persist_upload_entries(entries: list[dict[str, Any]]) -> None:
    """Persist valid entries via plain insert."""
    _persist_entries(entries, "insert")


def persist_upload_entries_with_overwrite(entries: list[dict[str, Any]]) -> None:
    """Persist entries via upsert (duplicate unique keys are overwritten)."""
    _persist_entries(entries, "upsert")
