# -*- coding: utf-8 -*-
from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.upload_intake_finalize import finalize_successful_excel_upload_intake


def test_finalize_successful_excel_upload_intake_side_effect_order() -> None:
    entries = [
        {
            "uploader_name": "U",
            "version": "v",
            "dataset_code": "pinjaman",
        }
    ]
    order: list[str] = []

    def _track_record(**_kwargs):
        order.append("record")

    def _track_delete(_folder, _tok):
        order.append("delete")

    def _track_remove(_path, **_kwargs):
        order.append("file")

    with (
        patch("services.upload_intake_finalize.record_upload_run", side_effect=_track_record),
        patch("services.upload_intake_finalize.delete_preview_session", side_effect=_track_delete),
        patch("services.upload_intake_finalize._safe_remove_file", side_effect=_track_remove),
    ):
        finalize_successful_excel_upload_intake(
            entries=entries,
            token_metadata={"dataset_slug": "pinjaman"},
            file_name="a.xlsx",
            upload_folder="/tmp/up",
            preview_token="tok",
            working_file_path="/tmp/up/f.xlsx",
            message=None,
        )

    assert order == ["record", "delete", "file"]


def test_finalize_skips_session_and_file_when_not_given() -> None:
    entries = [{"uploader_name": "U", "version": "v", "dataset_code": ""}]
    mock_record = MagicMock()
    mock_del = MagicMock()
    mock_rm = MagicMock()
    with (
        patch("services.upload_intake_finalize.record_upload_run", mock_record),
        patch("services.upload_intake_finalize.delete_preview_session", mock_del),
        patch("services.upload_intake_finalize._safe_remove_file", mock_rm),
    ):
        finalize_successful_excel_upload_intake(
            entries=entries,
            token_metadata=None,
            file_name=None,
            upload_folder=None,
            preview_token=None,
            working_file_path=None,
        )
    mock_record.assert_called_once()
    mock_del.assert_not_called()
    mock_rm.assert_not_called()
