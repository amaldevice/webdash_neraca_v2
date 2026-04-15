# -*- coding: utf-8 -*-
"""Thin read helpers over ``models.queries`` (P13)."""

from .entry_list import count_entries_for_list, fetch_entries_for_list

__all__ = ["count_entries_for_list", "fetch_entries_for_list"]
