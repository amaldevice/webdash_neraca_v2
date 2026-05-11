# -*- coding: utf-8 -*-
"""Unit tests for services.upload_flow (orchestration without full HTTP stack)."""
from __future__ import annotations

import os
from unittest.mock import patch

import models
from werkzeug.datastructures import ImmutableMultiDict

from services import upload_flow
from services import upload_parse
from services.upload_flow import (
    process_manual_input_post,
    process_upload_confirm,
    process_upload_post_file,
)
from services.upload_form import (
    collect_upload_file_errors,
    normalize_upload_action,
    parse_upload_form,
)
from services import upload_handlers


def _list_upload_runs(uploader_name: str, version: str):
    """ORM read of ``upload_runs`` for assertions (stable filter: uploader + version)."""
    from infrastructure.db import get_session, remove_scoped_session
    from infrastructure.orm_models import UploadRun
    from sqlalchemy import select

    session = get_session()
    try:
        return list(
            session.scalars(
                select(UploadRun)
                .where(
                    UploadRun.uploader_name == uploader_name,
                    UploadRun.version == version,
                )
                .order_by(UploadRun.id.asc())
            ).all()
        )
    finally:
        remove_scoped_session()


def _minimal_entry() -> dict:
    # ``periods.parse_period_date`` sets ``quarter`` for monthly rows; keep aligned so
    # duplicate SQL + unique upsert match ``build_manual_entry`` / parser output.
    return {
        "uploader_name": "U1",
        "version": "v1",
        "template_type": "excel",
        "data_type": "flow",
        "time_period": "monthly",
        "indicator_name": "GDP",
        "value": 1.0,
        "unit": None,
        "region_code": None,
        "year": 2024,
        "month": 3,
        "quarter": 1,
        "dataset_code": "",
    }


def _parse_payload_with_entries(entries: list) -> dict:
    return {
        "layout": "vertical",
        "source_mode": "headered",
        "header_row": 1,
        "source_rows": [],
        "source_columns": [],
        "entries": entries,
        "sample": [],
        "warnings": [],
        "invalid_rows": [],
    }


def test_normalize_upload_action():
    assert normalize_upload_action("") == "preview"
    assert normalize_upload_action("preview") == "preview"
    assert normalize_upload_action("SAVE") == "save"
    assert normalize_upload_action("direct_upload") == "direct_upload"
    assert normalize_upload_action("nope") == "preview"


def test_collect_upload_file_errors():
    from unittest.mock import MagicMock

    ok_file = MagicMock()
    ok_file.filename = "a.xlsx"
    assert collect_upload_file_errors("", "v1", ok_file, "flow", "monthly")
    assert collect_upload_file_errors("u", "", ok_file, "flow", "monthly")

    bad_file = MagicMock()
    bad_file.filename = "evil.exe"
    assert collect_upload_file_errors("u", "v1", bad_file, "flow", "monthly")

    errs_req = collect_upload_file_errors(
        "u", "v1", ok_file, "flow", "monthly", dataset_slug="", require_dataset=True
    )
    assert any("dataset" in e.lower() for e in errs_req)

    errs_bad_slug = collect_upload_file_errors(
        "u", "v1", ok_file, "flow", "monthly", dataset_slug="not-a-real-slug-xyz"
    )
    assert any("tidak dikenal" in e.lower() for e in errs_bad_slug)


def test_parse_upload_form():
    form = ImmutableMultiDict(
        [
            ("uploader", " A "),
            ("version", "v1"),
            ("data_type", "flow"),
            ("time_period", "monthly"),
            ("layout_override", "vertical"),
            ("dataset_slug", "pinjaman"),
            ("action", "confirm"),
            ("preview_token", "abc"),
            ("skip_duplicate_indexes", "0"),
            ("skip_duplicate_indexes", "2"),
        ]
    )
    fv, action, tok, skips = parse_upload_form(form)
    assert fv["uploader"] == "A"
    assert fv["dataset_slug"] == "pinjaman"
    assert action == "confirm"
    assert tok == "abc"
    assert skips == ["0", "2"]


def test_process_upload_confirm_missing_session(tmp_path):
    r = process_upload_confirm(
        str(tmp_path),
        "missing-token",
        {"uploader": "x", "version": "v1", "data_type": "flow", "time_period": "monthly", "layout_override": "auto"},
        [],
    )
    assert r.kind == "redirect"
    assert r.flashes[0][1] == "error"


def test_process_upload_confirm_inserts_without_duplicates(db_path, tmp_path):
    upload_dir = tmp_path / "u"
    upload_dir.mkdir()
    fp = upload_dir / "f.xlsx"
    fp.write_bytes(b"x")
    token_payload = {
        "file_path": str(fp),
        "file_name": "f.xlsx",
        "metadata": {
            "uploader": "U1",
            "version": "v1",
            "data_type": "flow",
            "time_period": "monthly",
        },
        "layout_override": "auto",
    }
    entry = _minimal_entry()
    parse_out = _parse_payload_with_entries([entry])
    form_values = {
        "uploader": "U1",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
        "layout_override": "auto",
    }

    with patch.object(upload_flow, "load_preview_session", return_value=token_payload):
        with patch.object(upload_parse, "parse_excel_payload", return_value=parse_out):
            with patch.object(upload_flow, "find_duplicate_entries_in_db", return_value=[]):
                with patch.object(upload_handlers, "delete_preview_session") as del_sess:
                        r = process_upload_confirm(str(upload_dir), "tok", form_values, [])

    assert r.kind == "redirect"
    assert r.pop_upload_session_token is True
    assert "berhasil" in r.flashes[0][0]
    assert models.get_total_entries_count() == 1
    del_sess.assert_called_once_with(str(upload_dir), "tok")
    assert not fp.exists()
    runs = _list_upload_runs("U1", "v1")
    assert len(runs) == 1
    ur = runs[0]
    assert ur.status == "success"
    assert ur.message is None
    assert ur.row_count == 1
    assert ur.file_name == "f.xlsx"
    assert ur.dataset_code == ""


def test_process_upload_confirm_records_single_upload_run_for_multi_row_insert(db_path, tmp_path):
    """``row_count`` on ``upload_runs`` matches inserted entry count; one audit row per confirm."""
    upload_dir = tmp_path / "u"
    upload_dir.mkdir()
    fp = upload_dir / "f.xlsx"
    fp.write_bytes(b"x")
    token_payload = {
        "file_path": str(fp),
        "file_name": "f.xlsx",
        "metadata": {
            "uploader": "U1",
            "version": "v1",
            "data_type": "flow",
            "time_period": "monthly",
        },
        "layout_override": "auto",
    }
    e2 = {
        **_minimal_entry(),
        "indicator_name": "CPI",
        "month": 4,
        "quarter": 2,
        "value": 2.0,
    }
    parse_out = _parse_payload_with_entries([_minimal_entry(), e2])
    form_values = {
        "uploader": "U1",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
        "layout_override": "auto",
    }

    with patch.object(upload_flow, "load_preview_session", return_value=token_payload):
        with patch.object(upload_parse, "parse_excel_payload", return_value=parse_out):
            with patch.object(upload_flow, "find_duplicate_entries_in_db", return_value=[]):
                with patch.object(upload_handlers, "delete_preview_session"):
                    r = process_upload_confirm(str(upload_dir), "tok", form_values, [])

    assert r.kind == "redirect"
    assert models.get_total_entries_count() == 2
    runs = _list_upload_runs("U1", "v1")
    assert len(runs) == 1
    assert runs[0].row_count == 2
    assert runs[0].status == "success"
    assert runs[0].file_name == "f.xlsx"


def test_process_upload_confirm_partial_duplicate_selection_overwrites_others(db_path, tmp_path):
    """User checks some duplicate candidates to skip; remaining duplicates should be overwritten."""
    upload_dir = tmp_path / "u"
    upload_dir.mkdir()
    fp = upload_dir / "f.xlsx"
    fp.write_bytes(b"x")
    token_payload = {
        "file_path": str(fp),
        "file_name": "f.xlsx",
        "metadata": {
            "uploader": "U1",
            "version": "v1",
            "data_type": "flow",
            "time_period": "monthly",
        },
        "layout_override": "auto",
    }
    e1 = _minimal_entry()
    e2 = {**_minimal_entry(), "indicator_name": "Other", "month": 4, "quarter": 2}
    parse_out = _parse_payload_with_entries([e1, e2])
    duplicates = [
        {"indicator_name": "GDP", "year": 2024, "month": 3, "quarter": 1},
        {"indicator_name": "Other", "year": 2024, "month": 4, "quarter": 2},
    ]
    form_values = {
        "uploader": "U1",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
        "layout_override": "auto",
    }

    with patch.object(upload_flow, "load_preview_session", return_value=token_payload):
        with patch.object(upload_parse, "parse_excel_payload", return_value=parse_out):
            with patch.object(upload_flow, "find_duplicate_entries_in_db", return_value=duplicates):
                with patch.object(upload_handlers, "delete_preview_session"):
                        r = process_upload_confirm(str(upload_dir), "tok", form_values, ["0"])

    assert r.kind == "redirect"
    assert r.pop_upload_session_token is True
    assert "ditimpa" in r.flashes[0][0]
    assert any("dikecualikan" in msg for msg, _ in r.flashes)
    assert models.get_total_entries_count() == 1


def test_process_upload_confirm_all_duplicate_rows_skipped_renders(db_path, tmp_path):
    """All file rows are duplicates marked to skip — nothing to insert."""
    upload_dir = tmp_path / "u"
    upload_dir.mkdir()
    fp = upload_dir / "f.xlsx"
    fp.write_bytes(b"x")
    token_payload = {
        "file_path": str(fp),
        "file_name": "f.xlsx",
        "metadata": {
            "uploader": "U1",
            "version": "v1",
            "data_type": "flow",
            "time_period": "monthly",
        },
        "layout_override": "auto",
    }
    entry = _minimal_entry()
    parse_out = _parse_payload_with_entries([entry])
    duplicates = [{"indicator_name": "GDP", "year": 2024, "month": 3, "quarter": 1}]

    with patch.object(upload_flow, "load_preview_session", return_value=token_payload):
        with patch.object(upload_parse, "parse_excel_payload", return_value=parse_out):
            with patch.object(upload_flow, "find_duplicate_entries_in_db", return_value=duplicates):
                r = process_upload_confirm(str(upload_dir), "tok", {}, ["0"])

    assert r.kind == "render"
    assert "Semua baris pada file adalah duplikasi terpilih" in r.flashes[0][0]
    assert models.get_total_entries_count() == 0


def test_process_upload_confirm_skip_duplicate_inserts_remaining_rows(db_path, tmp_path):
    """One row matches duplicate and is skipped; second row is inserted."""
    upload_dir = tmp_path / "u"
    upload_dir.mkdir()
    fp = upload_dir / "f.xlsx"
    fp.write_bytes(b"x")
    token_payload = {
        "file_path": str(fp),
        "file_name": "f.xlsx",
        "metadata": {
            "uploader": "U1",
            "version": "v1",
            "data_type": "flow",
            "time_period": "monthly",
        },
        "layout_override": "auto",
    }
    dup_row = _minimal_entry()
    new_row = {
        **dup_row,
        "indicator_name": "FreshIndicator",
        "value": 99.0,
    }
    parse_out = _parse_payload_with_entries([dup_row, new_row])
    duplicates = [{"indicator_name": "GDP", "year": 2024, "month": 3, "quarter": 1}]
    form_values = {
        "uploader": "U1",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
        "layout_override": "auto",
    }

    with patch.object(upload_flow, "load_preview_session", return_value=token_payload):
        with patch.object(upload_parse, "parse_excel_payload", return_value=parse_out):
            with patch.object(upload_flow, "find_duplicate_entries_in_db", return_value=duplicates):
                with patch.object(upload_handlers, "delete_preview_session"):
                        r = process_upload_confirm(str(upload_dir), "tok", form_values, ["0"])

    assert r.kind == "redirect"
    assert r.pop_upload_session_token is True
    assert any("dikecualikan" in msg for msg, _ in r.flashes)
    assert models.get_total_entries_count() == 1
    rows = models.query_data_entries(limit=5, indicator="FreshIndicator")
    assert len(rows) == 1


def test_process_upload_confirm_duplicate_without_skip_overwrites_existing_row(db_path, tmp_path):
    """If a duplicate isn't checked, confirmation overwrites the existing row."""
    upload_dir = tmp_path / "u"
    upload_dir.mkdir()
    fp = upload_dir / "f.xlsx"
    fp.write_bytes(b"x")
    token_payload = {
        "file_path": str(fp),
        "file_name": "f.xlsx",
        "metadata": {
            "uploader": "U1",
            "version": "v1",
            "data_type": "flow",
            "time_period": "monthly",
        },
        "layout_override": "auto",
    }
    entry = _minimal_entry()
    parse_out = _parse_payload_with_entries([entry])
    duplicates = [{"indicator_name": "GDP", "year": 2024, "month": 3, "quarter": 1}]
    existing = {**entry, "value": 9.99}
    models.insert_entries([existing])
    form_values = {
        "uploader": "U1",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
        "layout_override": "auto",
    }

    with patch.object(upload_flow, "load_preview_session", return_value=token_payload):
        with patch.object(upload_parse, "parse_excel_payload", return_value=parse_out):
            with patch.object(upload_flow, "find_duplicate_entries_in_db", return_value=duplicates):
                with patch.object(upload_handlers, "delete_preview_session"):
                        r = process_upload_confirm(str(upload_dir), "tok", form_values, [])

    assert r.kind == "redirect"
    assert r.pop_upload_session_token is True
    row = models.query_data_entries(limit=1, indicator="GDP")[0]
    assert row["value"] == entry["value"]
    assert "ditimpa" in r.flashes[0][0]


def test_process_upload_post_file_parse_error_deletes_file(tmp_path):
    upload_dir = tmp_path / "u"
    upload_dir.mkdir()
    dest = str(upload_dir / "bad.xlsx")
    with open(dest, "wb") as f:
        f.write(b"not-excel")

    form_values = {
        "uploader": "U1",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
        "layout_override": "auto",
    }

    def boom(*_a, **_k):
        raise ValueError("parse fail")

    with patch.object(upload_parse, "parse_excel_payload", side_effect=boom):
        r = process_upload_post_file(str(upload_dir), dest, "bad.xlsx", form_values, "preview")

    assert r.kind == "render"
    assert "Gagal membaca" in r.flashes[0][0]
    assert not os.path.isfile(dest)


def test_process_upload_post_file_preview_mocks_cache(db_path, tmp_path):
    upload_dir = tmp_path / "u"
    upload_dir.mkdir()
    dest = str(upload_dir / "ok.xlsx")
    with open(dest, "wb") as f:
        f.write(b"x")

    form_values = {
        "uploader": "U1",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
        "layout_override": "auto",
    }
    parse_out = _parse_payload_with_entries([_minimal_entry()])

    with patch.object(upload_parse, "parse_excel_payload", return_value=parse_out):
        with patch.object(upload_flow, "find_duplicate_entries_in_db", return_value=[]):
            with patch.object(upload_handlers, "cache_upload_preview", return_value="mocktok") as cache:
                r = process_upload_post_file(str(upload_dir), dest, "ok.xlsx", form_values, "preview")

    assert r.kind == "render"
    assert r.upload_preview_token == "mocktok"
    cache.assert_called_once()
    assert os.path.isfile(dest)


def test_process_manual_input_post_invalid(db_path):
    r = process_manual_input_post("a", "b", "not_a_type", "monthly", "2024-01", "x", "1")
    assert r.kind == "render"
    assert r.flashes


def test_process_manual_input_post_success(db_path):
    r = process_manual_input_post("M1", "v9", "flow", "monthly", "2024-06", "PIB", "99.5")
    assert r.kind == "redirect"
    assert models.get_total_entries_count() == 1
    runs = _list_upload_runs("M1", "v9")
    assert len(runs) == 1
    ur = runs[0]
    assert ur.status == "success"
    assert ur.message == "manual_input"
    assert ur.row_count == 1
    assert ur.file_name is None
    assert ur.dataset_code == ""


def test_process_manual_input_post_success_sets_dataset_code_from_slug(db_path):
    r = process_manual_input_post(
        "M2",
        "v1",
        "flow",
        "monthly",
        "2024-06",
        "PIB",
        "1",
        dataset_slug="pinjaman",
    )
    assert r.kind == "redirect"
    runs = _list_upload_runs("M2", "v1")
    assert len(runs) == 1
    assert runs[0].dataset_code == "pinjaman"
    assert runs[0].message == "manual_input"
    assert runs[0].row_count == 1


def test_process_manual_input_post_duplicate_detection(db_path):
    existing = _minimal_entry()
    existing["uploader_name"] = "SeedUser"
    existing["version"] = "v2"
    existing["value"] = 42.0
    models.insert_entries([existing])

    r = process_manual_input_post(
        "M1",
        "v9",
        "flow",
        "monthly",
        "2024-03",
        "GDP",
        "99.5",
        confirm_duplicate=False,
    )
    assert r.kind == "render"
    assert r.manual_duplicate is not None
    assert r.manual_duplicate["count"] >= 1
    assert r.manual_duplicate["indicator"] == "GDP"
    assert any("indikator" in msg.lower() for msg, _ in r.flashes)
    assert models.get_total_entries_count() == 1


def test_process_manual_input_post_duplicate_confirmation_inserts_row(db_path):
    existing = _minimal_entry()
    existing["uploader_name"] = "SeedUser"
    existing["version"] = "v2"
    existing["value"] = 42.0
    models.insert_entries([existing])

    r = process_manual_input_post(
        "M1",
        "v9",
        "flow",
        "monthly",
        "2024-03",
        "GDP",
        "99.5",
        confirm_duplicate=True,
    )
    assert r.kind == "redirect"
    assert models.get_total_entries_count() == 2
    runs = _list_upload_runs("M1", "v9")
    assert len(runs) == 1
    assert runs[0].message == "manual_input"
    assert runs[0].row_count == 1
    assert runs[0].status == "success"


def test_process_manual_input_post_require_dataset_empty_slug(db_path):
    r = process_manual_input_post(
        "M1",
        "v9",
        "flow",
        "monthly",
        "2024-03",
        "GDP",
        "1",
        require_dataset=True,
        dataset_slug="",
    )
    assert r.kind == "render"
    assert any("dataset" in msg.lower() for msg, _ in r.flashes)


def test_process_manual_input_post_unknown_dataset_slug(db_path):
    r = process_manual_input_post(
        "M1",
        "v9",
        "flow",
        "monthly",
        "2024-03",
        "GDP",
        "1",
        dataset_slug="not-a-slug",
    )
    assert r.kind == "render"
    assert any("tidak dikenal" in msg.lower() for msg, _ in r.flashes)
