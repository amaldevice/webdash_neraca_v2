# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.db import get_session, is_engine_initialized
from infrastructure.orm_models import DataEntry


def get_filter_options() -> Dict[str, List[str]]:
    """Get available options for filters (uploaders and indicators)"""
    if not is_engine_initialized():
        return {"uploaders": [], "indicators": []}
    try:
        session = get_session()
        uploaders = session.scalars(
            select(DataEntry.uploader_name).distinct().order_by(DataEntry.uploader_name)
        ).all()
        indicators = session.scalars(
            select(DataEntry.indicator_name).distinct().order_by(DataEntry.indicator_name)
        ).all()
        return {"uploaders": list(uploaders), "indicators": list(indicators)}
    except SQLAlchemyError:
        return {"uploaders": [], "indicators": []}
