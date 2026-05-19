# -*- coding: utf-8 -*-
"""Unit tests for entry_duplicate_key — Issue #89."""
from __future__ import annotations

import pytest

from services.upload_duplicates import entry_duplicate_key


def test_basic_dataset_code():
    entry = {
        "indicator_name": "X",
        "year": 2024,
        "month": 1,
        "quarter": None,
        "dataset_code": "abc",
    }
    assert entry_duplicate_key(entry) == ("X", 2024, 1, None, "abc")


def test_dataset_slug_fallback():
    """dataset_slug is legacy alias for dataset_code in incoming parsed entries."""
    entry = {
        "indicator_name": "X",
        "year": 2024,
        "month": 1,
        "quarter": None,
        "dataset_slug": "abc",
    }
    assert entry_duplicate_key(entry) == ("X", 2024, 1, None, "abc")


def test_dataset_code_takes_precedence_over_slug():
    entry = {
        "indicator_name": "X",
        "year": 2024,
        "month": 1,
        "quarter": None,
        "dataset_code": "code",
        "dataset_slug": "slug",
    }
    assert entry_duplicate_key(entry) == ("X", 2024, 1, None, "code")


def test_empty_dataset_code_falls_back_to_slug():
    entry = {
        "indicator_name": "X",
        "year": 2024,
        "month": 1,
        "quarter": None,
        "dataset_code": "",
        "dataset_slug": "fallback",
    }
    assert entry_duplicate_key(entry) == ("X", 2024, 1, None, "fallback")


def test_neither_code_nor_slug_returns_empty_string():
    entry = {
        "indicator_name": "X",
        "year": 2024,
        "month": 1,
        "quarter": None,
    }
    assert entry_duplicate_key(entry) == ("X", 2024, 1, None, "")


def test_strips_whitespace():
    entry = {
        "indicator_name": "X",
        "year": 2024,
        "month": 1,
        "quarter": None,
        "dataset_code": "  abc  ",
    }
    assert entry_duplicate_key(entry) == ("X", 2024, 1, None, "abc")
