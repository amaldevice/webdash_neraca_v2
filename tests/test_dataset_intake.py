# -*- coding: utf-8 -*-
from __future__ import annotations

from services.dataset_intake import resolve_dataset_for_intake


def test_resolve_dataset_for_intake_known_slug() -> None:
    r = resolve_dataset_for_intake("pinjaman")
    assert r.is_known
    assert r.slug == "pinjaman"
    assert r.dataset_code == "pinjaman"
    assert r.definition is not None
    assert r.definition.slug == "pinjaman"


def test_resolve_dataset_for_intake_unknown_slug() -> None:
    r = resolve_dataset_for_intake("not-a-real-slug-xyz")
    assert not r.is_known
    assert r.definition is None


def test_resolve_dataset_for_intake_empty() -> None:
    r = resolve_dataset_for_intake("")
    assert r.slug == ""
    assert r.dataset_code == ""
    assert r.definition is None
