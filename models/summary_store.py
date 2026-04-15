# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from contextlib import closing
from typing import Dict, Optional

from sqlalchemy import delete, desc, insert, select
from sqlalchemy.exc import SQLAlchemyError

from config import use_sqlalchemy
from infrastructure.db import get_session, is_engine_initialized, scoped_transaction
from infrastructure.orm_models import AggregatedSummary
from services.timeutil import utc_now_iso

from .connection import get_conn


def _use_sqlalchemy_summary() -> bool:
    return use_sqlalchemy() and is_engine_initialized()


def save_aggregated_summary(summary: Dict) -> None:
    payload = json.dumps(summary, ensure_ascii=False)
    now = utc_now_iso()
    if _use_sqlalchemy_summary():
        with scoped_transaction() as session:
            session.execute(delete(AggregatedSummary))
            session.execute(insert(AggregatedSummary).values(summary_json=payload, updated_at=now))
        return

    with closing(get_conn()) as conn:
        conn.execute("DELETE FROM aggregated_summary")
        conn.execute(
            """
            INSERT INTO aggregated_summary (summary_json, updated_at)
            VALUES (?, ?)
            """,
            (payload, now),
        )
        conn.commit()


def load_cached_summary() -> Optional[Dict]:
    if _use_sqlalchemy_summary():
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

    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT summary_json FROM aggregated_summary
            ORDER BY datetime(updated_at) DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        return json.loads(row["summary_json"])
