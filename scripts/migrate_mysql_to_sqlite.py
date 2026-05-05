# -*- coding: utf-8 -*-
"""One-way ETL: MySQL/PostgreSQL/other SQLAlchemy source -> SQLite backup (`data_entries` only).

Usage:
- Backup-only target file (default): `data_entries` from source DB copied into a timestamped SQLite file.
- Append mode: keep existing rows with ``--append`` (not default; default is replace via truncate).

Environment (optional defaults):
- `MYSQL_SOURCE_URL` - source SQLAlchemy URL if `--source-url` is omitted.
- `SQLITE_BACKUP_PATH` - explicit backup SQLite file path if `--sqlite-path` is omitted.
- `MYSQL_TARGET_URL` / `MIGRATE_TARGET_URL` / `DATABASE_URL` are fallback source candidates (non-sqlite first).

Security note:
Do not hardcode credentials. Set DSN values via protected environment variables or `.env`.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from sqlalchemy import create_engine, delete, insert, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT = _SCRIPT_DIR.parent if _SCRIPT_DIR.name == "scripts" else _SCRIPT_DIR
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import BASE_DIR  # noqa: E402
from infrastructure.orm_models import Base, DataEntry  # noqa: E402

_LOG = logging.getLogger("migrate_mysql_to_sqlite")
_TABLE_NAME = "data_entries"
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


def _load_dotenv_if_available() -> None:
    try:
        from config import _load_dotenv_into_os_environ

        _load_dotenv_into_os_environ()
        return
    except Exception:
        pass

    try:
        from dotenv import load_dotenv

        load_dotenv(_ROOT / ".env", override=False)
        extra = os.environ.get("DOTENV_PATH", "").strip()
        if extra:
            load_dotenv(extra, override=False)
    except Exception:
        return


def _sqlite_url_from_path(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def _default_sqlite_path() -> Path:
    raw = (os.environ.get("SQLITE_BACKUP_PATH") or "").strip()
    if raw:
        return Path(raw).expanduser()

    backup_dir = Path(BASE_DIR) / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return backup_dir / f"data_backup_{stamp}.db"


def _resolve_codebase_source_url() -> str:
    try:
        from config import database_url as cfg_database_url

        resolved = (cfg_database_url() or "").strip()
        if resolved and not resolved.startswith("sqlite"):
            return resolved
    except Exception:
        return ""
    return ""


def _resolve_source_url(cli_url: str | None) -> str:
    if cli_url and cli_url.strip():
        return cli_url.strip()
    for key in ("MYSQL_SOURCE_URL", "MYSQL_TARGET_URL", "MIGRATE_TARGET_URL", "DATABASE_URL"):
        raw = (os.environ.get(key) or "").strip()
        if raw and not raw.startswith("sqlite"):
            return raw
    resolved = _resolve_codebase_source_url()
    if resolved:
        return resolved
    return ""


def _create_engine(url: str) -> Engine:
    return create_engine(url, future=True)


def _ensure_source_table_exists(engine: Engine) -> None:
    inspector = inspect(engine)
    has_table = inspector.has_table(_TABLE_NAME)
    if not has_table:
        raise RuntimeError(f"Table {_TABLE_NAME} does not exist in source database.")


def _stats_data_entries(engine: Engine) -> tuple[int, float]:
    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM data_entries")).scalar_one()
        s = conn.execute(text("SELECT COALESCE(SUM(value), 0) FROM data_entries")).scalar_one()
    return int(n), float(s or 0.0)


def _ensure_sqlite_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def _truncate_target(session: Session) -> None:
    session.execute(delete(DataEntry))
    session.commit()
    _LOG.info("Target data_entries table truncated.")


def _fetch_data_entries_chunk(source: Engine, last_id: int, limit: int) -> Sequence[Mapping[str, Any]]:
    cols = ", ".join(_DATA_ENTRY_COLUMNS)
    stmt = text(f"SELECT {cols} FROM data_entries WHERE id > :last_id ORDER BY id LIMIT :lim")
    with source.connect() as conn:
        return conn.execute(stmt, {"last_id": last_id, "lim": limit}).mappings().all()


def _migrate_data_entries(source: Engine, target_session_factory: sessionmaker[Session], chunk_size: int) -> int:
    migrated = 0
    last_id = 0
    while True:
        rows = _fetch_data_entries_chunk(source, last_id=last_id, limit=chunk_size)
        if not rows:
            break

        payload = [dict(r) for r in rows]
        with target_session_factory() as session:
            session.execute(insert(DataEntry), payload)
            session.commit()

        migrated += len(payload)
        last_id = payload[-1]["id"]
        _LOG.info("data_entries: migrated %d rows", migrated)
    return migrated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-url",
        default=None,
        help="Source SQLAlchemy URL (default: MYSQL_SOURCE_URL / MYSQL_TARGET_URL / MIGRATE_TARGET_URL / non-sqlite DATABASE_URL).",
    )
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=None,
        help="Output SQLite backup path (default: SQLITE_BACKUP_PATH env or /backups/data_backup_<timestamp>.db).",
    )
    parser.add_argument(
        "--truncate-target",
        action="store_true",
        help="DELETE current target data before loading (default safe for fresh backup files too).",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append into existing target table. Use with caution because unique constraints can fail on duplicates.",
    )
    parser.add_argument("--chunk-size", type=int, default=500, help="Rows per insert transaction (default 500).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only compare source vs current target row counts and SUM(value); no writes.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG logging.")
    args = parser.parse_args(argv)

    _load_dotenv_if_available()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")

    source_url = _resolve_source_url(args.source_url)
    if not source_url:
        _LOG.error(
            "Missing source URL. Use --source-url or set MYSQL_SOURCE_URL / MYSQL_TARGET_URL / MIGRATE_TARGET_URL / "
            "non-sqlite DATABASE_URL."
        )
        return 2

    sqlite_path = args.sqlite_path or _default_sqlite_path()
    if not sqlite_path.suffix:
        sqlite_path = sqlite_path.with_suffix(".db")

    if not args.dry_run and not args.append and not args.truncate_target and sqlite_path.is_file():
        _LOG.error("Target backup file exists: %s. Use --append or --truncate-target to proceed.", sqlite_path)
        return 2

    source_engine = _create_engine(source_url)
    target_path = sqlite_path.expanduser().resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_engine = _create_engine(_sqlite_url_from_path(target_path))
    TargetSession = sessionmaker(target_engine, class_=Session, autoflush=False, expire_on_commit=False)

    try:
        _ensure_source_table_exists(source_engine)
        source_rows, source_sum = _stats_data_entries(source_engine)
        _LOG.info("Source data_entries: %d rows, sum(value)=%.6f", source_rows, source_sum)

        _ensure_sqlite_schema(target_engine)
        target_before_rows, target_before_sum = _stats_data_entries(target_engine)

        if args.dry_run:
            _LOG.info("Target current data_entries: %d rows, sum(value)=%.6f", target_before_rows, target_before_sum)
            _LOG.info("Dry-run complete. No writes.")
            return 0

        if args.truncate_target:
            with TargetSession() as session:
                _truncate_target(session)

        migrated = _migrate_data_entries(source_engine, TargetSession, max(1, args.chunk_size))
        _LOG.info("Done. Inserted data_entries rows=%d", migrated)

        target_rows, target_sum = _stats_data_entries(target_engine)
        expected_rows = source_rows if not args.append else (target_before_rows + source_rows)
        expected_sum = source_sum if not args.append else (target_before_sum + source_sum)
        if target_rows != expected_rows or abs(target_sum - expected_sum) > 1e-6:
            _LOG.warning(
                "Verify mismatch: expected rows=%s (source=%s, target_before=%s) sum=%.6f (source_sum=%.6f, target_before_sum=%.6f) | target rows=%s sum=%s",
                expected_rows,
                source_rows,
                target_before_rows if args.append else 0,
                expected_sum,
                source_sum,
                target_before_sum if args.append else 0,
                target_rows,
                target_sum,
            )
            return 1

        if args.append and expected_rows > 0:
            _LOG.info("Verify ok for append mode: target rows/sum increased as expected.")
        else:
            _LOG.info("Verify ok: target rows/sum match source.")
    except SQLAlchemyError as exc:
        _LOG.error("SQLAlchemy error: %s", exc)
        return 1
    finally:
        source_engine.dispose()
        target_engine.dispose()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
