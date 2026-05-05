# Repository Structure Overview

## Lokasi Kritis

- `app.py`: factory aplikasi (`create_app`) + alias helper untuk compat test.
- `.env` / `.env.example`: konfigurasi environment dan DSN.
- `wsgi.py`: entry point WSGI.
- `infrastructure/`: engine DB, session lifecycle, ORM model inti.
- `models/`: query/mutation/filter/browse service data.
- `services/`: logika domain (upload, parser, manual entry, chart, analitik periodik, preview, templates).
- `excel_parser/`: pipeline parser Excel (universal + dataset-aware).
- `routes/`: endpoint web app (landing, upload/manual, preview, dashboard, data-management, ekspor).
- `templates/`, `static/`, `assets/`: UI + stylesheet.
- `tests/`: unit, simple tests, e2e dan bug hunting.
- `scripts/`: utility CLI untuk migrate/flush/template.
- `docs/`: dokumentasi operasional + plan.

## Jalur Request Penting

1. `app.py` memanggil `create_app()`.
2. `register_routes` (`routes/__init__.py`) mendaftarkan:
   - `routes/pages.py`
   - `routes/upload_routes.py`
   - `routes/manage.py`
3. Endpoint upload:
   - validasi input → simpan file/temp session → parse via `excel_parser.payload` → normalisasi → cache preview (`services/upload_preview`) → konfirmasi → persist (`services/upload_flow` + `models.mutations`).
4. Endpoint manual:
   - build payload (`services/manual_entries`) → validasi → `insert`/`upsert`.
5. Dashboard/Preview/Data-management:
   - parameter filter masuk ke `services/data_filters` + query di `models/queries`.
6. Analisa periode:
   - endpoint di `manage.py` memakai `services/period_comparisons` + `services/period_comparison_calculators` + exporter workbook.

## Struktur Folder (fungsi inti)

- `models/connection.py`: kompatibilitas inisialisasi/connector.
- `models/queries.py`: query data, listing, ringkasan, filter by period/value/uploader.
- `models/mutations.py`: CRUD + upsert dialect-aware.
- `services/upload_flow.py`: orchestrator upload + duplicate workflow + response serializer.
- `services/upload_preview.py`: sesi preview disk + filter duplicate DB.
- `services/template_service.py` + `services/dataset_catalog.py`: template dataset-aware.
- `services/period_analysis_workbook.py`: ekspor xlsx hasil analisis periodik.
- `services/timeutil.py` + `periods.py`: format waktu dan normalisasi periode.
- `excel_parser/*`: parser universial, long-format, layout detect (horizontal/vertical/mixed).

## Struktur Dokumen

- `docs/README_DOCS.md`: index/operasional utama.
- `docs/planning.md`: stub sinkron dokumentasi + plan.
- `.cursor/plans/bps_data_management_system_bd94389d.plan.md`: todolist arsitektur.
- `docs/superpowers/*`: rencana gelombang fitur dan RFC.
- `docs/troubleshooting/*`: runbook error utama.

## Script Utilities

- `scripts/migrate_sqlite_to_mysql.py`
- `scripts/migrate_mysql_to_sqlite.py`
- `scripts/flush_db.py`
- `scripts/build_rekap_long_templates.py`
- `scripts/agent_browser_upload_smoke.ps1`
- `scripts/playwright_cli_smoke.ps1`

Catatan:

- `scripts/*.ps1` dipakai untuk smoke/manual flow.
- `scripts/*.py` tidak dipanggil di route web runtime (hanya operasi ops).

