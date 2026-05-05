# -*- coding: utf-8 -*-
"""Persist lightweight upload audit rows (Fase 4)."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from infrastructure.db import is_engine_initialized, scoped_transaction
from infrastructure.orm_models import UploadRun
from services.timeutil import utc_now_iso

_log = logging.getLogger(__name__)


def record_upload_run(
    *,
    uploader_name: str,
    version: str,
    dataset_code: str,
    file_name: str | None,
    status: str,
    message: str | None = None,
    row_count: int | None = None,
) -> None:
    """Best-effort insert; failures are logged and swallowed (must not break upload flow)."""
    if not is_engine_initialized():
        return
    row = UploadRun(
        created_at=utc_now_iso(),
        uploader_name=uploader_name,
        version=version,
        dataset_code=(dataset_code or "").strip(),
        file_name=file_name,
        status=status,
        message=message,
        row_count=row_count,
    )
    try:
        with scoped_transaction() as session:
            session.add(row)
    except SQLAlchemyError as exc:
        _log.warning("record_upload_run failed: %s", exc)
