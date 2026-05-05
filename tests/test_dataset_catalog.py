"""Tests for services.dataset_catalog."""

from __future__ import annotations

import pytest

from services.dataset_catalog import get_dataset, get_dataset_or_none, list_dataset_slugs


def test_list_slugs_seven_ordered() -> None:
    slugs = list_dataset_slugs()
    assert len(slugs) == 7
    assert slugs[0] == "pinjaman"
    assert "kartu_kredit" in slugs


def test_get_dataset_kartu_source_sheet_trailing_space() -> None:
    d = get_dataset("kartu_kredit")
    assert d.source_sheet == "Kartu kredit "
    assert d.time_period_mode == "monthly"


def test_get_dataset_unknown() -> None:
    with pytest.raises(KeyError, match="Dataset tidak dikenal"):
        get_dataset("resume")


def test_get_dataset_or_none() -> None:
    assert get_dataset_or_none("pinjaman") is not None
    assert get_dataset_or_none("nope") is None


def test_sample_rows_align_with_headers() -> None:
    for slug in list_dataset_slugs():
        d = get_dataset(slug)
        w = len(d.required_template_headers)
        for row in d.sample_rows:
            assert len(row) == w
