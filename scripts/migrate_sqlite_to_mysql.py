# -*- coding: utf-8 -*-
"""
One-way ETL: SQLite file (legacy ``data.db``) -> target SQLAlchemy DSN (MySQL 8 / MariaDB, or PostgreSQL).

- Chunked ``INSERT`` with one transaction per chunk (default chunk size 500).
- Use ``--truncate-target`` before load when the target schema already has rows (avoids PK / unique clashes).
- ``--dry-run`` only compares row counts + ``SUM(value)`` on ``data_entries``; no writes.

Environment (optional defaults):

- ``SQLITE_SOURCE_PATH`` - path to ``.db`` file if ``--sqlite-path`` omitted.
- ``MYSQL_TARGET_URL`` / ``MIGRATE_TARGET_URL`` - target DSN if ``--target-url`` omitted.

Do not commit credentials; pass URL via env or a protected env file on the office server.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from sqlalchemy import create_engine, delete, insert, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Repo root (parent of scripts/)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import BASE_DIR  # noqa: E402
from infrastructure.orm_models import DataEntry  # noqa: E402

_LOG = logging.getLogger("migrate_sqlite_to_mysql")

_DATA_ENTRY_COLUMNS: tuple[str, ...] = (
    "id",
    "uploader_name",
    "version",
    "template_type",
    "data_type",
    "time_period",
    "indicator_name",
    "value",
    "unit",
    "region_code",
    "year",
    "month",
    "quarter",
    "created_at",
)
def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def _default_sqlite_path() -> Path:
    raw = (os.environ.get("SQLITE_SOURCE_PATH") or "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path(BASE_DIR) / "data.db"


def _resolve_target_url(cli_value: str | None) -> str:
    if cli_value and cli_value.strip():
        return cli_value.strip()
    for key in ("MIGRATE_TARGET_URL", "MYSQL_TARGET_URL", "DATABASE_URL"):
        raw = (os.environ.get(key) or "").strip()
        if raw and not raw.startswith("sqlite"):
            return raw
    return ""


def _stats_data_entries(engine: Engine) -> tuple[int, float]:
    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM data_entries")).scalar_one()
        s = conn.execute(text("SELECT COALESCE(SUM(value), 0) FROM data_entries")).scalar_one()
    return int(n), float(s or 0.0)


def _verify(source: Engine, target: Engine) -> None:
    src_n, src_sum = _stats_data_entries(source)
    tgt_n, tgt_sum = _stats_data_entries(target)
    _LOG.info(
        "Verify data_entries: source rows=%d sum(value)=%.6f | target rows=%d sum(value)=%.6f",
        src_n,
        src_sum,
        tgt_n,
        tgt_sum,
    )
    if src_n != tgt_n or abs(src_sum - tgt_sum) > 1e-6:
        raise SystemExit(f"Mismatch data_entries: rows {src_n}!={tgt_n} or sum {src_sum}!={tgt_sum}")


def _truncate_target(session: Session) -> None:
    session.execute(delete(DataEntry))
    session.commit()
    _LOG.info("Target data_entries table truncated.")


def _fetch_data_entries_chunk(source: Engine, offset: int, limit: int) -> Sequence[Mapping[str, Any]]:
    cols = ", ".join(_DATA_ENTRY_COLUMNS)
    stmt = text(f"SELECT {cols} FROM data_entries ORDER BY id LIMIT :lim OFFSET :off")
    with source.connect() as conn:
        return conn.execute(stmt, {"lim": limit, "off": offset}).mappings().all()


def _migrate_data_entries(source: Engine, SessionTarget: sessionmaker[Session], chunk_size: int) -> int:
    with source.connect() as conn:
        total = int(conn.execute(text("SELECT COUNT(*) FROM data_entries")).scalar_one())
    inserted = 0
    offset = 0
    while offset < total:
        rows = _fetch_data_entries_chunk(source, offset, chunk_size)
        if not rows:
            break
        payload = [dict(r) for r in rows]
        with SessionTarget() as session:
            session.execute(insert(DataEntry), payload)
            session.commit()
        inserted += len(payload)
        offset += len(payload)
        _LOG.info("data_entries: migrated %d / %d rows", inserted, total)
    return inserted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=None,
        help=f"Source SQLite file (default: SQLITE_SOURCE_PATH env or {{BASE_DIR}}/data.db).",
    )
    parser.add_argument(
        "--target-url",
        default=None,
        help="Target SQLAlchemy URL (default: MIGRATE_TARGET_URL or MYSQL_TARGET_URL env, non-sqlite DATABASE_URL).",
    )
    parser.add_argument("--chunk-size", type=int, default=500, help="Rows per insert transaction (default 500).")
    parser.add_argument(
        "--truncate-target",
        action="store_true",
        help="DELETE all rows in target data_entries before loading.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only log counts and SUM(value); no writes.",
    )
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    sqlite_path = args.sqlite_path or _default_sqlite_path()
    if not sqlite_path.is_file():
        _LOG.error("SQLite file not found: %s", sqlite_path)
        return 2

    target_url = _resolve_target_url(args.target_url)
    if not target_url:
        _LOG.error(
            "Missing target URL: pass --target-url or set MIGRATE_TARGET_URL / MYSQL_TARGET_URL "
            "(non-sqlite DATABASE_URL also accepted).",
        )
        return 2

    source_engine = create_engine(_sqlite_url(sqlite_path), future=True)
    target_engine = create_engine(target_url, future=True)
    SessionTarget = sessionmaker(target_engine, class_=Session, autoflush=False, expire_on_commit=False)

    try:
        src_n, src_sum = _stats_data_entries(source_engine)
        _LOG.info(
            "Source %s - data_entries: %d rows, sum(value)=%.6f",
            sqlite_path,
            src_n,
            src_sum,
        )

        if args.dry_run:
            tgt_n, tgt_sum = _stats_data_entries(target_engine)
            _LOG.info(
                "Target (current) - data_entries: %d rows, sum(value)=%.6f",
                tgt_n,
                tgt_sum,
            )
            return 0

        tgt_n0, _ = _stats_data_entries(target_engine)
        if tgt_n0 and not args.truncate_target:
            _LOG.warning(
                "Target already has %d data_entries row(s). Use --truncate-target for full replace, "
                "or expect unique-key failures / verify mismatch.",
                tgt_n0,
            )

        if args.truncate_target:
            with SessionTarget() as session:
                _truncate_target(session)

        n_entries = _migrate_data_entries(source_engine, SessionTarget, max(1, args.chunk_size))
        _LOG.info("Done. Inserted data_entries rows=%d", n_entries)
        _verify(source_engine, target_engine)
    finally:
        source_engine.dispose()
        target_engine.dispose()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
