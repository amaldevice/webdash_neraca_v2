# -*- coding: utf-8 -*-
"""Flush only table content for `data_entries` while keeping schema intact.

Run: `python flush_db.py` (interactive),
or `python flush_db.py --targets sqlite|mysql|both --yes`.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT = _SCRIPT_DIR.parent if _SCRIPT_DIR.name == "scripts" else _SCRIPT_DIR
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_DEFAULT_SQLITE_PATH = _ROOT / "data.db"
_TABLE_NAME = "data_entries"
_LOG = logging.getLogger("flush_db")


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


def _resolve_codebase_mysql_url() -> str:
    try:
        from config import database_url as cfg_database_url

        resolved = (cfg_database_url() or "").strip()
        if resolved and not resolved.startswith("sqlite"):
            return resolved
    except Exception:
        return ""
    return ""


def _mask_db_url(url: str) -> str:
    """Hide credentials in logs/CLI output."""
    try:
        parsed = urlsplit(url)
        if not parsed.username:
            return url
        host = parsed.netloc.split("@", 1)[-1]
        creds = parsed.username
        if parsed.password is not None:
            creds = f"{creds}:***"
        return urlunsplit((parsed.scheme, f"{creds}@{host}", parsed.path, parsed.query, parsed.fragment))
    except Exception:
        return url


def _is_interactive() -> bool:
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _sqlite_url_from_path(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def _resolve_sqlite_url(cli_url: str | None, cli_path: Path | None) -> str:
    if cli_url and cli_url.strip():
        value = cli_url.strip()
        if value.startswith("sqlite://"):
            return value
        return _sqlite_url_from_path(Path(value))
    if cli_path is not None:
        return _sqlite_url_from_path(cli_path)
    raw_path = (os.environ.get("SQLITE_SOURCE_PATH") or "").strip()
    if raw_path:
        return _sqlite_url_from_path(Path(raw_path))
    database_url = (os.environ.get("DATABASE_URL") or "").strip()
    if database_url.startswith("sqlite"):
        return database_url
    return _sqlite_url_from_path(_DEFAULT_SQLITE_PATH)


def _resolve_mysql_url(cli_url: str | None) -> str:
    if cli_url and cli_url.strip():
        return cli_url.strip()
    for key in ("MYSQL_TARGET_URL", "MIGRATE_TARGET_URL", "DATABASE_URL"):
        raw = (os.environ.get(key) or "").strip()
        if raw and not raw.startswith("sqlite"):
            return raw
    resolved = _resolve_codebase_mysql_url()
    if resolved:
        return resolved
    return ""


def _create_engine(url: str) -> Engine:
    return create_engine(url, future=True)


def _ensure_table_exists(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(_TABLE_NAME):
        raise RuntimeError(f"Table {_TABLE_NAME} does not exist in target database.")


def _count_rows(engine: Engine) -> int:
    with engine.connect() as conn:
        value = conn.execute(text(f"SELECT COUNT(*) FROM {_TABLE_NAME}")).scalar_one()
    return int(value or 0)


def _sqlite_file_from_url(url: str) -> Path | None:
    try:
        parsed = make_url(url)
    except Exception:
        return None
    if parsed.drivername != "sqlite":
        return None
    db = parsed.database
    if not isinstance(db, str) or not db.strip() or db == ":memory:":
        return None
    path = Path(unquote(db)).expanduser()
    if not path.is_absolute():
        path = _ROOT / path
    return path


def _is_path_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def _check_target(label: str, key: str, url: str) -> dict[str, Any]:
    state: dict[str, Any] = {
        "label": label,
        "key": key,
        "url": url,
        "ready": False,
        "reason": None,
        "rows": 0,
        "engine": None,
    }

    if not url.strip():
        state["reason"] = "URL target tidak diset."
        return state

    if key == "sqlite":
        sqlite_path = _sqlite_file_from_url(url)
        if sqlite_path is None:
            state["reason"] = "URL SQLite tidak valid untuk file database."
            return state
        if not _is_path_exists(sqlite_path):
            state["reason"] = f"File SQLite tidak ditemukan: {sqlite_path}"
            return state

    try:
        engine = _create_engine(url)
        _ensure_table_exists(engine)
        state["rows"] = _count_rows(engine)
        state["engine"] = engine
        state["ready"] = True
        return state
    except (SQLAlchemyError, RuntimeError, OSError) as exc:
        state["reason"] = str(exc)
        return state


def _reset_identity(conn: Any, engine: Engine) -> None:
    dialect = engine.dialect.name
    if dialect == "sqlite":
        conn.execute(text("DELETE FROM sqlite_sequence WHERE name = :name"), {"name": _TABLE_NAME})
        return
    if dialect in {"mysql", "mariadb"}:
        conn.execute(text(f"ALTER TABLE {_TABLE_NAME} AUTO_INCREMENT = 1"))
        return
    if dialect == "postgresql":
        # Best-effort fallback. Unsupported/blocked by permissions on managed DBs can be ignored.
        conn.execute(text(f"ALTER SEQUENCE IF EXISTS {_TABLE_NAME}_id_seq RESTART WITH 1"))


def _flush_database(engine: Engine, *, reset_identities: bool) -> tuple[int, int]:
    before = _count_rows(engine)
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {_TABLE_NAME}"))
        if reset_identities:
            try:
                _reset_identity(conn, engine)
            except SQLAlchemyError as exc:
                _LOG.warning("Identity reset failed; data deleted successfully: %s", exc)
    after = _count_rows(engine)
    return before, after


def _parse_targets(value: str | None) -> set[str]:
    if value is None:
        return set()
    if value == "both":
        return {"sqlite", "mysql"}
    return {value}


def _line_for_state(state: dict[str, Any], *, dry_run: bool) -> str:
    if not state["ready"]:
        return f"{state['label']}: {state['reason']} | url={_mask_db_url(state['url'])}"
    if dry_run:
        return f"{state['label']}: {state['rows']} rows | url={_mask_db_url(state['url'])}"
    return f"{state['label']}: {state['rows']} rows (will be deleted) | url={_mask_db_url(state['url'])}"


def _print_target_status(prechecks: dict[str, dict[str, Any]]) -> None:
    print("Pemeriksaan awal target database:")
    print(_line_for_state(prechecks["mysql"], dry_run=True))
    print(_line_for_state(prechecks["sqlite"], dry_run=True))


def _select_targets_interactive(prechecks: dict[str, dict[str, Any]]) -> set[str]:
    while True:
        print("")
        print("Pilih target flush:")
        print("  1) MySQL")
        print("  2) SQLite")
        print("  3) Keduanya (MySQL + SQLite)")
        choice = input("Pilih [1/2/3]: ").strip()

        if choice == "1":
            selected = {"mysql"}
        elif choice == "2":
            selected = {"sqlite"}
        elif choice == "3":
            selected = {"mysql", "sqlite"}
        else:
            print("Pilihan tidak valid. Input harus 1, 2, atau 3.")
            continue

        not_ready = [k for k in selected if not prechecks[k]["ready"]]
        if not_ready:
            names = ", ".join(k.upper() for k in not_ready)
            print(f"Target belum siap: {names}. Cek pesan status di atas.")
            continue
        return selected


def _confirm_or_exit(lines: list[str], *, auto_yes: bool) -> None:
    print("Rencana flush:")
    for line in lines:
        print(f" - {line}")
    if auto_yes:
        return
    if not _is_interactive():
        raise SystemExit(
            "Mode non-interaktif terdeteksi. Tambah --yes untuk menjalankan flush tanpa konfirmasi."
        )
    answer = input("Ketik 'flush' untuk melanjutkan penghapusan permanen: ").strip().lower()
    if answer != "flush":
        raise SystemExit("Operation cancelled.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--targets",
        choices=("sqlite", "mysql", "both"),
        default=None,
        help="Target DB: sqlite, mysql, or both. Jika dihilangkan -> mode interaktif.",
    )
    parser.add_argument("--sqlite-url", default=None, help="SQLAlchemy URL for SQLite target.")
    parser.add_argument("--sqlite-path", type=Path, default=None, help="SQLite file path if not using sqlite-url.")
    parser.add_argument(
        "--mysql-url",
        default=None,
        help="SQLAlchemy URL for MySQL target (default: MYSQL_TARGET_URL / MIGRATE_TARGET_URL / non-sqlite DATABASE_URL).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show planned row counts only; do not delete.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation and flush immediately.",
    )
    parser.add_argument(
        "--reset-identities",
        action="store_true",
        help="Try to reset table identity/autoincrement after delete.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG logging.")
    args = parser.parse_args(argv)

    _load_dotenv_if_available()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")

    requested = _parse_targets(args.targets)
    # Cek dua target terlebih dulu agar user tahu status sebelum memilih menu.
    prechecks: dict[str, dict[str, Any]] = {
        "mysql": _check_target("MySQL", "mysql", _resolve_mysql_url(args.mysql_url)),
        "sqlite": _check_target("SQLite", "sqlite", _resolve_sqlite_url(args.sqlite_url, args.sqlite_path)),
    }

    if not requested:
        if not any(p["ready"] for p in prechecks.values()):
            print("Tidak ada target yang siap flush.")
            _print_target_status(prechecks)
            return 2
        if not _is_interactive():
            print("Mode non-interaktif. Jika ingin flush tanpa interaksi, gunakan --targets dan --yes.")
            _print_target_status(prechecks)
            return 2
        _print_target_status(prechecks)
        selected = _select_targets_interactive(prechecks)
    else:
        selected = requested
        not_ready = [k for k in selected if not prechecks[k]["ready"]]
        if not_ready:
            _print_target_status(prechecks)
            missing = ", ".join(k.upper() for k in not_ready)
            print(f"Target tidak siap: {missing}.")
            return 2

    prepared: list[tuple[str, str, str, Engine, int]] = []
    for key in sorted(selected):
        state = prechecks[key]
        prepared.append((state["label"], key, state["url"], state["engine"], state["rows"]))

    summary_lines = [_line_for_state(prechecks[key], dry_run=args.dry_run) for key in sorted(selected)]

    if args.dry_run:
        print("Mode DRY-RUN aktif. Tidak ada data yang dihapus.")
        for line in summary_lines:
            print(line)
        return 0

    _confirm_or_exit(summary_lines, auto_yes=args.yes)

    failed: list[str] = []
    for label, key, url, engine, before in prepared:
        try:
            _, after = _flush_database(engine, reset_identities=args.reset_identities)
            _LOG.info(
                "%s selesai: rows %s -> %s (deleted %s) | url=%s",
                label,
                before,
                after,
                before - after,
                _mask_db_url(url),
            )
            if key == "sqlite":
                _LOG.info("SQLite flush done.")
            else:
                _LOG.info("MySQL flush done.")
        except (SQLAlchemyError, RuntimeError) as exc:
            failed.append(f"{label}: {exc}")
            _LOG.error("Flush failed for %s (%s): %s", label, _mask_db_url(url), exc)
        finally:
            engine.dispose()

    if failed:
        _LOG.error("Flush done with errors: %s", "; ".join(failed))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
