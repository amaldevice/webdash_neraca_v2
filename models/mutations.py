# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import sqlite3
from contextlib import closing
from typing import Callable, Dict, Iterable, List, Optional

from periods import parse_period_date
from services.timeutil import utc_now_iso
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from config import use_sqlalchemy
from infrastructure.db import is_engine_initialized, scoped_transaction
from infrastructure.orm_models import AggregatedSummary, DataEntry

from .connection import get_conn
from .data_filters import _build_data_entry_filter_clauses, build_data_entry_filter_sqlalchemy

_log = logging.getLogger(__name__)

MutationFn = Callable[[sqlite3.Connection], Optional[sqlite3.Cursor]]


def _to_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_valid_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        value_float = float(value)
    except (TypeError, ValueError):
        return None
    return value_float


def _use_sqlalchemy_writes() -> bool:
    return use_sqlalchemy() and is_engine_initialized()


def _execute_mutation(
    operation: str,
    mutation_fn: MutationFn,
    *,
    raise_on_error: bool = False,
) -> Optional[sqlite3.Cursor]:
    """Run a mutation block with a fresh connection and commit."""
    try:
        with closing(get_conn()) as conn:
            cursor = mutation_fn(conn)
            conn.commit()
            return cursor
    except sqlite3.Error as exc:
        _log.warning("%s failed: %s", operation, exc)
        if raise_on_error:
            raise
        return None


def _run_mutation(operation: str, mutation_fn: MutationFn, *, default: int = 0) -> int:
    """Run mutation and return cursor.rowcount (or default on error)."""
    cursor = _execute_mutation(operation, mutation_fn)
    if cursor is None:
        return default
    return cursor.rowcount if cursor.rowcount is not None else default


def _compose_insert_values(entry: Dict, now: str):
    return (
        entry["uploader_name"],
        entry["version"],
        entry.get("template_type"),
        entry.get("data_type"),
        entry.get("time_period"),
        entry["indicator_name"],
        _to_float(entry.get("value")),
        entry.get("unit"),
        entry.get("region_code"),
        entry.get("year"),
        entry.get("month"),
        entry.get("quarter"),
        entry.get("created_at", now),
    )


def _insert_entries_payload(conn: sqlite3.Connection, entries: Iterable[Dict], now: str) -> Optional[sqlite3.Cursor]:
    cursor = conn.cursor()
    for entry in entries:
        cursor.execute(
            """
            INSERT INTO data_entries (
                uploader_name, version, template_type, data_type, time_period,
                indicator_name, value, unit, region_code, year, month, quarter, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _compose_insert_values(entry, now),
        )
    return cursor


def _upsert_entries_payload(conn: sqlite3.Connection, entries: Iterable[Dict], now: str) -> Optional[sqlite3.Cursor]:
    cursor = conn.cursor()
    for entry in entries:
        cursor.execute(
            """
            INSERT INTO data_entries (
                uploader_name, version, template_type, data_type, time_period,
                indicator_name, value, unit, region_code, year, month, quarter, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uploader_name, version, indicator_name, year, month, quarter)
            DO UPDATE SET
                template_type = excluded.template_type,
                data_type = excluded.data_type,
                time_period = excluded.time_period,
                value = excluded.value,
                unit = excluded.unit,
                region_code = excluded.region_code,
                created_at = excluded.created_at
            """,
            _compose_insert_values(entry, now),
        )
    return cursor


def _update_data_entry_payload(
    conn: sqlite3.Connection,
    entry_id: str,
    new_value: float,
) -> Optional[sqlite3.Cursor]:
    return conn.execute(
        "UPDATE data_entries SET value = ? WHERE id = ?",
        (new_value, entry_id),
    )


def _delete_entry_by_id_payload(conn: sqlite3.Connection, entry_id: str) -> Optional[sqlite3.Cursor]:
    return conn.execute("DELETE FROM data_entries WHERE id = ?", (entry_id,))


def _build_id_placeholders(count: int) -> str:
    return ",".join(["?"] * count)


def _bulk_delete_entries_payload(
    conn: sqlite3.Connection,
    entry_ids: List[str],
) -> Optional[sqlite3.Cursor]:
    placeholders = _build_id_placeholders(len(entry_ids))
    query = f"DELETE FROM data_entries WHERE id IN ({placeholders})"
    return conn.execute(query, entry_ids)


def insert_entries(entries: Iterable[Dict]) -> None:
    now = utc_now_iso()
    entries_list = list(entries)
    if not entries_list:
        return
    if _use_sqlalchemy_writes():
        from infrastructure.dialect_upsert import insert_data_entries

        try:
            with scoped_transaction() as session:
                insert_data_entries(session, entries_list, now)
        except IntegrityError as exc:
            _log.warning("insert_entries failed: %s", exc)
            raise sqlite3.IntegrityError(str(exc)) from exc
        except SQLAlchemyError as exc:
            _log.warning("insert_entries failed: %s", exc)
            raise
        return
    _execute_mutation(
        "insert_entries",
        lambda conn: _insert_entries_payload(conn, entries_list, now),
        raise_on_error=True,
    )


def upsert_entries(entries: Iterable[Dict]) -> None:
    now = utc_now_iso()
    entries_list = list(entries)
    if not entries_list:
        return
    if _use_sqlalchemy_writes():
        from infrastructure.dialect_upsert import upsert_data_entries

        try:
            with scoped_transaction() as session:
                upsert_data_entries(session, entries_list, now)
        except SQLAlchemyError as exc:
            _log.warning("upsert_entries failed: %s", exc)
            raise
        return
    _execute_mutation(
        "upsert_entries",
        lambda conn: _upsert_entries_payload(conn, entries_list, now),
        raise_on_error=True,
    )


def delete_data_entry(entry_id: str) -> bool:
    """Delete a single data entry by ID"""
    if _use_sqlalchemy_writes():
        try:
            with scoped_transaction() as session:
                res = session.execute(delete(DataEntry).where(DataEntry.id == int(entry_id)))
                return (res.rowcount or 0) > 0
        except SQLAlchemyError as exc:
            _log.warning("delete_data_entry failed: %s", exc)
            return False
    affected_rows = _run_mutation("delete_data_entry", lambda conn: _delete_entry_by_id_payload(conn, entry_id))
    return affected_rows > 0


def clear_all_data() -> bool:
    """Clear all data from database tables (for testing)"""
    if _use_sqlalchemy_writes():
        try:
            with scoped_transaction() as session:
                session.execute(delete(DataEntry))
                session.execute(delete(AggregatedSummary))
            return True
        except SQLAlchemyError as exc:
            _log.warning("clear_all_data failed: %s", exc)
            return False
    try:
        with closing(get_conn()) as conn:
            conn.execute("DELETE FROM data_entries")
            conn.execute("DELETE FROM aggregated_summary")
            conn.commit()
            return True
    except sqlite3.Error as exc:
        _log.warning("clear_all_data failed: %s", exc)
        return False


def delete_data_by_filter(
    data_type: Optional[str] = None,
    time_period: Optional[str] = None,
    uploader: Optional[str] = None,
    indicator: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    value_min: Optional[float] = None,
    value_max: Optional[float] = None,
) -> int:
    """Delete data entries based on filters"""
    if _use_sqlalchemy_writes():
        where = build_data_entry_filter_sqlalchemy(
            data_type, time_period, uploader, indicator, period_start, period_end, value_min, value_max
        )
        if where is None:
            return 0
        try:
            with scoped_transaction() as session:
                res = session.execute(delete(DataEntry).where(where))
                return res.rowcount or 0
        except SQLAlchemyError as exc:
            _log.warning("delete_data_by_filter failed: %s", exc)
            return 0

    clauses, params = _build_data_entry_filter_clauses(
        data_type, time_period, uploader, indicator, period_start, period_end, value_min, value_max
    )

    if not clauses:
        return 0

    query = "DELETE FROM data_entries WHERE " + " AND ".join(clauses)

    with closing(get_conn()) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount


def update_data_entry(entry_id: str, new_value: float) -> bool:
    """Update the value of a data entry"""
    parsed_value = _to_valid_float(new_value)
    if parsed_value is None:
        _log.warning("update_data_entry failed: invalid value %r", new_value)
        return False

    if _use_sqlalchemy_writes():
        try:
            with scoped_transaction() as session:
                res = session.execute(
                    update(DataEntry).where(DataEntry.id == int(entry_id)).values(value=parsed_value)
                )
                return (res.rowcount or 0) > 0
        except SQLAlchemyError as exc:
            _log.warning("update_data_entry failed: %s", exc)
            return False

    affected_rows = _run_mutation(
        "update_data_entry",
        lambda conn: _update_data_entry_payload(conn, entry_id, parsed_value),
    )
    return affected_rows > 0


def update_data_entry_full(entry_id: str, data: Dict) -> bool:
    """Update all fields of a data entry"""
    if _use_sqlalchemy_writes():
        try:
            with scoped_transaction() as session:
                res = session.execute(
                    update(DataEntry)
                    .where(DataEntry.id == int(entry_id))
                    .values(
                        uploader_name=data["uploader_name"],
                        version=data["version"],
                        indicator_name=data["indicator_name"],
                        value=data["value"],
                        data_type=data["data_type"],
                        time_period=data["time_period"],
                    )
                )
                return (res.rowcount or 0) > 0
        except (SQLAlchemyError, KeyError, TypeError) as exc:
            _log.warning("update_data_entry_full failed: %s", exc)
            return False
    try:
        with closing(get_conn()) as conn:
            cursor = conn.execute(
                """
                UPDATE data_entries SET
                    uploader_name = ?,
                    version = ?,
                    indicator_name = ?,
                    value = ?,
                    data_type = ?,
                    time_period = ?
                WHERE id = ?
                """,
                (
                    data["uploader_name"],
                    data["version"],
                    data["indicator_name"],
                    data["value"],
                    data["data_type"],
                    data["time_period"],
                    entry_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
    except (sqlite3.Error, KeyError, TypeError) as exc:
        _log.warning("update_data_entry_full failed: %s", exc)
        return False


def insert_single_entry(
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    period_date: str,
    indicator: str,
    value: float,
) -> bool:
    """Insert a single data entry"""
    if _use_sqlalchemy_writes():
        from sqlalchemy import insert

        try:
            year, month, quarter = parse_period_date(time_period, period_date)
            with scoped_transaction() as session:
                session.execute(
                    insert(DataEntry).values(
                        uploader_name=uploader,
                        version=version,
                        template_type="manual_crud",
                        data_type=data_type.lower() or "flow",
                        time_period=time_period.lower() or "monthly",
                        indicator_name=indicator,
                        value=value,
                        unit=None,
                        region_code=None,
                        year=year,
                        month=month,
                        quarter=quarter,
                        created_at=utc_now_iso(),
                    )
                )
            return True
        except (SQLAlchemyError, ValueError, TypeError) as exc:
            _log.warning("insert_single_entry failed: %s", exc)
            return False
    try:
        year, month, quarter = parse_period_date(time_period, period_date)

        with closing(get_conn()) as conn:
            cursor = conn.execute(
                """
                INSERT INTO data_entries (
                    uploader_name, version, template_type, data_type, time_period,
                    indicator_name, value, unit, region_code, year, month, quarter, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uploader,
                    version,
                    "manual_crud",
                    data_type.lower() or "flow",
                    time_period.lower() or "monthly",
                    indicator,
                    value,
                    None,
                    None,
                    year,
                    month,
                    quarter,
                    utc_now_iso(),
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
    except (sqlite3.Error, ValueError, TypeError) as exc:
        _log.warning("insert_single_entry failed: %s", exc)
        return False


def bulk_delete_entries(entry_ids: List[str]) -> int:
    """Delete multiple data entries by their IDs"""
    if not entry_ids:
        return 0
    if _use_sqlalchemy_writes():
        ids = [int(i) for i in entry_ids]
        try:
            with scoped_transaction() as session:
                res = session.execute(delete(DataEntry).where(DataEntry.id.in_(ids)))
                return res.rowcount or 0
        except SQLAlchemyError as exc:
            _log.warning("bulk_delete_entries failed: %s", exc)
            return 0
    return _run_mutation(
        "bulk_delete_entries",
        lambda conn: _bulk_delete_entries_payload(conn, entry_ids),
    )


def bulk_update_entries(entry_ids: List[str], updates: Dict) -> int:
    """Update multiple data entries with the same values"""
    if not entry_ids or not updates:
        return 0

    if _use_sqlalchemy_writes():
        vals: Dict = {}
        for field, value in updates.items():
            if field in ["uploader_name", "version", "indicator_name", "data_type", "time_period"]:
                vals[field] = value
            elif field == "value":
                parsed_value = _to_valid_float(value)
                if parsed_value is None:
                    _log.warning("bulk_update_entries failed: invalid value %r", value)
                    return 0
                vals["value"] = parsed_value

        if not vals:
            return 0

        ids = [int(i) for i in entry_ids]
        try:
            with scoped_transaction() as session:
                res = session.execute(update(DataEntry).where(DataEntry.id.in_(ids)).values(**vals))
                return res.rowcount or 0
        except (SQLAlchemyError, ValueError, TypeError) as exc:
            _log.warning("bulk_update_entries failed: %s", exc)
            return 0

    try:
        with closing(get_conn()) as conn:
            set_parts = []
            params = []

            for field, value in updates.items():
                if field in ["uploader_name", "version", "indicator_name", "data_type", "time_period"]:
                    set_parts.append(f"{field} = ?")
                    params.append(value)
                elif field == "value":
                    parsed_value = _to_valid_float(value)
                    if parsed_value is None:
                        _log.warning("bulk_update_entries failed: invalid value %r", value)
                        return 0
                    set_parts.append("value = ?")
                    params.append(parsed_value)

            if not set_parts:
                return 0

            set_clause = ", ".join(set_parts)

            placeholders = ",".join("?" * len(entry_ids))
            params.extend(entry_ids)

            query = f"UPDATE data_entries SET {set_clause} WHERE id IN ({placeholders})"

            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    except (sqlite3.Error, ValueError, TypeError) as exc:
        _log.warning("bulk_update_entries failed: %s", exc)
        return 0
