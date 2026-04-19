# -*- coding: utf-8 -*-
"""
Sinkronkan skema DB dengan revisi Alembic `002_dataset` (kolom `dataset_code` + `upload_runs`).

Kasus umum di MySQL: tabel `data_entries` sudah ada dari deploy lama, tetapi `alembic_version` kosong
→ `alembic upgrade head` mencoba `001_initial` lagi → error 1050. Solusi: `stamp 001_initial` lalu `upgrade head`.

Kasus lain: `alembic` sudah di 001 tetapi kode app baru → error 1054 `dataset_code` → cukup `upgrade head`.

Prasyarat: `DATABASE_URL` / `ALEMBIC_DATABASE_URL` benar; backup sebelum `--yes`.

  python scripts/apply_dataset_code_migration.py --dry-run
  python scripts/apply_dataset_code_migration.py --yes
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.chdir(_ROOT)

from alembic import command  # noqa: E402
from alembic.config import Config as AlembicConfig  # noqa: E402
from alembic.runtime.migration import MigrationContext  # noqa: E402
from sqlalchemy import create_engine, inspect  # noqa: E402

from config import database_url  # noqa: E402


def _alembic_cfg() -> AlembicConfig:
    return AlembicConfig(str(_ROOT / "alembic.ini"))


def _current_revision(url: str) -> str | None:
    engine = create_engine(url, future=True)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        return ctx.get_current_revision()


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply dataset_code / upload_runs schema via Alembic.")
    parser.add_argument("--dry-run", action="store_true", help="Hanya laporkan rencana.")
    parser.add_argument("--yes", action="store_true", help="Jalankan stamp (bila perlu) + upgrade.")
    args = parser.parse_args()

    url = database_url()
    engine = create_engine(url, future=True)
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    has_entries = "data_entries" in tables
    cols = {c["name"] for c in insp.get_columns("data_entries")} if has_entries else set()
    has_dataset_code = "dataset_code" in cols
    rev = _current_revision(url)

    print(f"DSN (ringkas): …@{url.split('@')[-1]}" if "@" in url else f"DSN: {url}")
    print(f"alembic revision: {rev!r}")
    print(f"data_entries: {has_entries}, dataset_code: {has_dataset_code}")

    if has_dataset_code:
        if rev == "002_dataset":
            print("Skema sudah selaras 002_dataset.")
            return 0
        has_upload_runs = "upload_runs" in tables
        if not has_upload_runs:
            print("Kolom dataset_code ada; tabel upload_runs belum — perlu alembic upgrade head.")
            if args.dry_run:
                return 0
            if not args.yes:
                print("Tambahkan --yes untuk menjalankan upgrade head.")
                return 2
            command.upgrade(_alembic_cfg(), "head")
            print("Selesai: alembic upgrade head")
            return 0
        print(
            "Kolom dataset_code dan upload_runs ada; alembic_version belum 002_dataset — stamp revisi."
        )
        if args.dry_run:
            return 0
        if not args.yes:
            print("Tambahkan --yes untuk: alembic stamp 002_dataset")
            return 2
        command.stamp(_alembic_cfg(), "002_dataset")
        print("Selesai: alembic stamp 002_dataset")
        return 0

    if not has_entries:
        print("Belum ada data_entries → python -m alembic upgrade head")
        if args.dry_run or not args.yes:
            if not args.yes:
                print("Tambahkan --yes untuk menjalankan upgrade head.")
            return 0 if args.dry_run else 2
        command.upgrade(_alembic_cfg(), "head")
        print("Selesai: alembic upgrade head")
        return 0

    # data_entries ada, dataset_code belum
    if rev is None:
        print("Rencana: alembic stamp 001_initial lalu alembic upgrade head")
    elif rev == "001_initial":
        print("Rencana: alembic upgrade head")
    else:
        print(
            f"Revisi {rev!r} tidak didukung skrip ini (kolom dataset_code hilang). "
            "Lihat docs/troubleshooting/mysql-schema-dataset-code-and-alembic.md"
        )
        return 3

    if args.dry_run:
        return 0
    if not args.yes:
        print("Tambahkan --yes untuk menjalankan.")
        return 2

    cfg = _alembic_cfg()
    if rev is None:
        command.stamp(cfg, "001_initial")
        print("Selesai: alembic stamp 001_initial")
    command.upgrade(cfg, "head")
    print("Selesai: alembic upgrade head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
