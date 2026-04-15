# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Dict, Optional

from sqlalchemy import delete, desc, insert, select
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.db import get_session, is_engine_initialized, scoped_transaction
from infrastructure.orm_models import AggregatedSummary
from services.timeutil import utc_now_iso


def save_aggregated_summary(summary: Dict) -> None:
    if not is_engine_initialized():
        raise RuntimeError("save_aggregated_summary requires SQLAlchemy engine.")
    payload = json.dumps(summary, ensure_ascii=False)
    now = utc_now_iso()
    with scoped_transaction() as session:
        session.execute(delete(AggregatedSummary))
        session.execute(insert(AggregatedSummary).values(summary_json=payload, updated_at=now))


def load_cached_summary() -> Optional[Dict]:
    if not is_engine_initialized():
        return None
    try:
        session = get_session()
        stmt = (
            select(AggregatedSummary.summary_json)
            .order_by(desc(AggregatedSummary.updated_at))
            .limit(1)
        )
        row = session.execute(stmt).scalar_one_or_none()
        if row is None:
            return None
        return json.loads(row)
    except (SQLAlchemyError, json.JSONDecodeError, TypeError):
        return None
