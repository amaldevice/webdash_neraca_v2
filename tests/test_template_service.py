"""Tests for services.template_service."""

from __future__ import annotations

from io import BytesIO

import pandas as pd

from services.dataset_catalog import dataset_workbook_sheet_title, get_dataset, list_dataset_slugs
from services.template_service import (
    build_multi_dataset_reference_workbook,
    generate_workbook_for_dataset,
    workbook_to_bytes,
)


def test_generate_single_dataset_workbook_roundtrip() -> None:
    wb = generate_workbook_for_dataset("simpanan", with_sample=True, include_notes=True)
    data = workbook_to_bytes(wb)
    xl = pd.ExcelFile(BytesIO(data), engine="openpyxl")
    assert "README" in xl.sheet_names
    sheet_title = dataset_workbook_sheet_title(get_dataset("simpanan"))
    assert sheet_title in xl.sheet_names
    df = pd.read_excel(xl, sheet_name=sheet_title, header=0)
    assert list(df.columns) == list(get_dataset("simpanan").required_template_headers)


def test_multi_dataset_workbook_has_all_tabs() -> None:
    wb = build_multi_dataset_reference_workbook(with_sample=True)
    names = set(wb.sheetnames)
    assert "README" in names
    for slug in list_dataset_slugs():
        if slug == "universal":
            continue
        title = dataset_workbook_sheet_title(get_dataset(slug))
        assert title in names


def test_workbook_bytes_non_empty() -> None:
    wb = generate_workbook_for_dataset("ecommerce", include_notes=False)
    assert len(workbook_to_bytes(wb)) > 500


def test_build_template_file_response_universal_filename() -> None:
    from services.template_service import build_template_file_response

    resp = build_template_file_response("universal")
    cd = resp.headers.get("Content-Disposition", "")
    assert "template_universal" in cd


def test_build_template_file_response_attachment() -> None:
    from services.template_service import build_template_file_response

    resp = build_template_file_response("pinjaman")
    assert resp.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    cd = resp.headers.get("Content-Disposition", "")
    assert "attachment" in cd
    assert "template_rekap_pinjaman" in cd
    assert len(resp.get_data()) > 400
