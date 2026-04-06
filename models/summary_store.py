# -*- coding: utf-8 -*-
import json
from contextlib import closing
from typing import Dict, Optional

from services.timeutil import utc_now_iso

from .connection import get_conn


def save_aggregated_summary(summary: Dict) -> None:
    payload = json.dumps(summary, ensure_ascii=False)
    now = utc_now_iso()
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
