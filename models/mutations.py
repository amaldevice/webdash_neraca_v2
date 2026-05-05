# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from periods import parse_period_date
from services.timeutil import utc_now_iso
from sqlalchemy import delete, insert, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from infrastructure.db import is_engine_initialized, scoped_transaction
from infrastructure.orm_models import DataEntry

from .data_filters import build_data_entry_filter_sqlalchemy

_log = logging.getLogger(__name__)


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


def _require_engine() -> None:
    if not is_engine_initialized():
        raise RuntimeError("Database engine not initialized; call init_engine() first.")


def insert_entries(entries: Iterable[Dict]) -> None:
    now = utc_now_iso()
    entries_list = list(entries)
    if not entries_list:
        return
    _require_engine()
    from infrastructure.dialect_upsert import insert_data_entries

    try:
        with scoped_transaction() as session:
            insert_data_entries(session, entries_list, now)
    except IntegrityError:
        raise
    except SQLAlchemyError as exc:
        _log.warning("insert_entries failed: %s", exc)
        raise


def upsert_entries(entries: Iterable[Dict]) -> None:
    now = utc_now_iso()
    entries_list = list(entries)
    if not entries_list:
        return
    _require_engine()
    from infrastructure.dialect_upsert import upsert_data_entries

    try:
        with scoped_transaction() as session:
            upsert_data_entries(session, entries_list, now)
    except SQLAlchemyError as exc:
        _log.warning("upsert_entries failed: %s", exc)
        raise


def delete_data_entry(entry_id: str) -> bool:
    """Delete a single data entry by ID"""
    _require_engine()
    try:
        with scoped_transaction() as session:
            res = session.execute(delete(DataEntry).where(DataEntry.id == int(entry_id)))
            return (res.rowcount or 0) > 0
    except SQLAlchemyError as exc:
        _log.warning("delete_data_entry failed: %s", exc)
        return False


def clear_all_data() -> bool:
    """Clear all data from database tables (for testing)"""
    _require_engine()
    try:
        with scoped_transaction() as session:
            session.execute(delete(DataEntry))
        return True
    except SQLAlchemyError as exc:
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
    dataset_code: Optional[str] = None,
) -> int:
    """Delete data entries based on filters"""
    _require_engine()
    where = build_data_entry_filter_sqlalchemy(
        data_type,
        time_period,
        uploader,
        indicator,
        period_start,
        period_end,
        value_min,
        value_max,
        dataset_code,
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


def update_data_entry(entry_id: str, new_value: float) -> bool:
    """Update the value of a data entry"""
    parsed_value = _to_valid_float(new_value)
    if parsed_value is None:
        _log.warning("update_data_entry failed: invalid value %r", new_value)
        return False

    _require_engine()
    try:
        with scoped_transaction() as session:
            res = session.execute(
                update(DataEntry).where(DataEntry.id == int(entry_id)).values(value=parsed_value)
            )
            return (res.rowcount or 0) > 0
    except SQLAlchemyError as exc:
        _log.warning("update_data_entry failed: %s", exc)
        return False


def update_data_entry_full(entry_id: str, data: Dict) -> bool:
    """Update all fields of a data entry"""
    _require_engine()
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


def insert_single_entry(
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    period_date: str,
    indicator: str,
    value: float,
    *,
    dataset_code: str = "",
) -> bool:
    """Insert a single data entry"""
    _require_engine()
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
                    dataset_code=(dataset_code or "").strip(),
                )
            )
        return True
    except (SQLAlchemyError, ValueError, TypeError) as exc:
        _log.warning("insert_single_entry failed: %s", exc)
        return False


def bulk_delete_entries(entry_ids: List[str]) -> int:
    """Delete multiple data entries by their IDs"""
    if not entry_ids:
        return 0
    _require_engine()
    ids = [int(i) for i in entry_ids]
    try:
        with scoped_transaction() as session:
            res = session.execute(delete(DataEntry).where(DataEntry.id.in_(ids)))
            return res.rowcount or 0
    except SQLAlchemyError as exc:
        _log.warning("bulk_delete_entries failed: %s", exc)
        return 0


def bulk_update_entries(entry_ids: List[str], updates: Dict) -> int:
    """Update multiple data entries with the same values"""
    if not entry_ids or not updates:
        return 0

    _require_engine()
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
