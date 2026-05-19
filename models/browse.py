# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.orm_models import DataEntry
from models.read_session import with_read_session

_EMPTY_FILTER: Dict[str, List[str]] = {"uploaders": [], "indicators": [], "dataset_codes": []}


def get_filter_options(*, session: Session | None = None) -> Dict[str, List[str]]:
    """Get available options for filters (uploaders, indicators, dataset_code)."""

    def _query(sess: Session) -> Dict[str, List[str]]:
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

    return with_read_session(_query, default=_EMPTY_FILTER, session=session)
