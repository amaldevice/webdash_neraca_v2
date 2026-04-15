# -*- coding: utf-8 -*-
"""Portable bulk insert / upsert for ``data_entries`` (SQLAlchemy 2.0, P5)."""
from __future__ import annotations

from typing import Any, Dict, Sequence

from sqlalchemy import insert
from sqlalchemy.orm import Session

from infrastructure.orm_models import DataEntry


def _coerce_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def entry_to_row_mapping(entry: Dict[str, Any], now: str) -> Dict[str, Any]:
    """Map upload/manual payload dict to ORM column names (same as legacy ``_compose_insert_values``)."""
    return {
        "uploader_name": entry["uploader_name"],
        "version": entry["version"],
        "template_type": entry.get("template_type"),
        "data_type": entry.get("data_type"),
        "time_period": entry.get("time_period"),
        "indicator_name": entry["indicator_name"],
        "value": _coerce_float(entry.get("value")),
        "unit": entry.get("unit"),
        "region_code": entry.get("region_code"),
        "year": entry.get("year"),
        "month": entry.get("month"),
        "quarter": entry.get("quarter"),
        "created_at": entry.get("created_at", now),
    }


def insert_data_entries(session: Session, entries: Sequence[Dict[str, Any]], now: str) -> None:
    """Plain ``INSERT`` for each row (fails on unique violation)."""
    mappings = [entry_to_row_mapping(e, now) for e in entries]
    session.execute(insert(DataEntry), mappings)


def upsert_data_entries(session: Session, entries: Sequence[Dict[str, Any]], now: str) -> None:
    """Insert or update on unique (uploader, version, indicator, year, month, quarter)."""
    dialect = session.get_bind().dialect.name
    for entry in entries:
        row = entry_to_row_mapping(entry, now)
        if dialect == "mysql":
            _upsert_one_mysql(session, row)
        else:
            _upsert_one_sqlite_postgresql(session, row, dialect)


def _upsert_one_mysql(session: Session, row: Dict[str, Any]) -> None:
    from sqlalchemy.dialects.mysql import insert as mysql_insert

    ins = mysql_insert(DataEntry).values(**row)
    stmt = ins.on_duplicate_key_update(
        template_type=ins.inserted.template_type,
        data_type=ins.inserted.data_type,
        time_period=ins.inserted.time_period,
        value=ins.inserted.value,
        unit=ins.inserted.unit,
        region_code=ins.inserted.region_code,
        created_at=ins.inserted.created_at,
    )
    session.execute(stmt)


def _upsert_one_sqlite_postgresql(session: Session, row: Dict[str, Any], dialect: str) -> None:
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
    else:
        from sqlalchemy.dialects.sqlite import insert as dialect_insert

    ins = dialect_insert(DataEntry).values(**row)
    stmt = ins.on_conflict_do_update(
        index_elements=[
            DataEntry.uploader_name,
            DataEntry.version,
            DataEntry.indicator_name,
            DataEntry.year,
            DataEntry.month,
            DataEntry.quarter,
        ],
        set_={
            "template_type": ins.excluded.template_type,
            "data_type": ins.excluded.data_type,
            "time_period": ins.excluded.time_period,
            "value": ins.excluded.value,
            "unit": ins.excluded.unit,
            "region_code": ins.excluded.region_code,
            "created_at": ins.excluded.created_at,
        },
    )
    session.execute(stmt)
