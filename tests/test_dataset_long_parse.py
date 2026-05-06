# -*- coding: utf-8 -*-
"""Fase 5: parser long-format per dataset (template katalog)."""
from __future__ import annotations

import pytest

from excel_parser import parse_excel_payload
from services.dataset_catalog import get_dataset, list_dataset_slugs
from services.template_service import generate_workbook_for_dataset, workbook_to_bytes


@pytest.mark.parametrize("slug", [s for s in list_dataset_slugs() if s != "universal"])
def test_parse_generated_template_long_format_roundtrip(slug: str, tmp_path) -> None:
    wb = generate_workbook_for_dataset(slug, with_sample=True, include_notes=False)
    raw = workbook_to_bytes(wb)
    p = tmp_path / f"{slug}.xlsx"
    p.write_bytes(raw)
    definition = get_dataset(slug)
    payload = parse_excel_payload(
        str(p),
        "U-long",
        "v-ds-1",
        "flow",
        definition.time_period_mode,
        dataset_slug=slug,
    )
    assert payload.get("source_mode") == "long"
    assert payload.get("layout") == "long"
    entries = payload.get("entries") or []
    assert len(entries) >= 1
    assert all(e.get("uploader_name") == "U-long" for e in entries)
    assert all(e.get("template_type") == "long" for e in entries)
    assert all(e.get("time_period") == definition.time_period_mode for e in entries)
    assert all(e.get("indicator_name") for e in entries)
    assert all(e.get("value") is not None for e in entries)


def test_parse_universal_generated_roundtrip(tmp_path) -> None:
    slug = "universal"
    wb = generate_workbook_for_dataset(slug, with_sample=True, include_notes=False)
    raw = workbook_to_bytes(wb)
    p = tmp_path / "univ.xlsx"
    p.write_bytes(raw)
    payload = parse_excel_payload(
        str(p),
        "U-uni",
        "v-u1",
        "flow",
        "monthly",
        dataset_slug=slug,
    )
    assert payload.get("source_mode") == "long"
    entries = payload.get("entries") or []
    assert len(entries) >= 1
    assert entries[0]["template_type"] == "universal_long"
    assert entries[0].get("dataset_code") == "universal"
    assert "|" in entries[0]["indicator_name"]


def test_parse_legacy_horizontal_without_dataset_slug(tmp_path) -> None:
    """Regresi: format wide klasik tanpa slug dataset tetap jalan."""
    import pandas as pd

    path = tmp_path / "wide.xlsx"
    df = pd.DataFrame(
        [
            ["Indikator", pd.Timestamp("2024-01-01")],
            ["GDP", 42.0],
        ]
    )
    df.to_excel(path, index=False, header=False, engine="openpyxl")
    payload = parse_excel_payload(
        str(path),
        "Legacy",
        "v1",
        "flow",
        "monthly",
        layout_override="horizontal",
        dataset_slug="",
    )
    assert payload.get("source_mode") in ("headered", "legacy")
    assert len(payload.get("entries") or []) >= 1
