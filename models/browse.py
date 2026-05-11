# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.db import get_session, is_engine_initialized
from infrastructure.orm_models import DataEntry


def get_filter_options(*, session: Session | None = None) -> Dict[str, List[str]]:
    """Get available options for filters (uploaders, indicators, dataset_code)."""
    if session is None and not is_engine_initialized():
        return {"uploaders": [], "indicators": [], "dataset_codes": []}
    try:
        sess = session if session is not None else get_session()
    except SQLAlchemyError:
        return {"uploaders": [], "indicators": [], "dataset_codes": []}
    try:
        uploaders = sess.scalars(
            select(DataEntry.uploader_name).distinct().order_by(DataEntry.uploader_name)
        ).all()
        indicators = sess.scalars(
            select(DataEntry.indicator_name).distinct().order_by(DataEntry.indicator_name)
        ).all()
        codes = sess.scalars(
            select(DataEntry.dataset_code).distinct().order_by(DataEntry.dataset_code)
        ).all()
        return {
            "uploaders": list(uploaders),
            "indicators": list(indicators),
            "dataset_codes": list(codes),
        }
    except SQLAlchemyError:
        return {"uploaders": [], "indicators": [], "dataset_codes": []}
