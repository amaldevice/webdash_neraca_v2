# Integrasi dan Dependensi

## Integrasi Database

- Aplikasi beroperasi via SQLAlchemy Engine (`infrastructure/db.py`).
- Sumber DSN:
  - `DATABASE_URL` (primary),
  - fallback `DATABASE_URL` lama untuk compatibility,
  - alias opsional: `MYSQL_TARGET_URL`, `MYSQL_SOURCE_URL`, `MIGRATE_TARGET_URL`.
- Environment produksi menuntut `DATABASE_URL` eksplicit saat `FLASK_ENV=production`.

## Integrasi File & Storage

- Upload/preview menggunakan folder `uploads/` (`config.py` + service).
- Template static:
  - `static/templates/upload_template.xlsx`,
  - `static/templates/rekap_dataset_long_templates.xlsx` (artifact).
- Preview sementara disimpan di `_preview_sessions` pada disk agar multi-worker aman.

## Integrasi Komponen Excel & Dataset

- Parser pipeline:
  - `excel_parser/payload.py` -> `excel_parser/normalize.py` -> `services/manual_entries.py`.
- Dataset catalog:
  - `services/dataset_catalog.py` menyediakan metadata per dataset,
  - `services/template_service.py` menghasilkan template per dataset.
- Template download endpoint:
  - `GET /upload/template/<dataset_slug>`.

## Integrasi UI/API

- Endpoints utama:
  - `/upload`, `/upload/manual`, `/upload/confirm`, `/upload/template/<slug>`
  - `/preview-data`, `/data-management`, `/dashboard`, `/export`, `/export-period-analysis`.
- Export dan chart memakai endpoint yang menerima filter period/range agar konsisten.

## Integrasi Pengujian

- Unit/integration: pytest.
- Smoke/e2e: Playwright (script `npm run test:e2e`).
- Browser script dan file log test disimpan di `.playwright-cli/` dan `tests/*/logs`.

## Integrasi Operasional

- Dokumentasi migrasi dan runbook troubleshooting terpusat:
  - `docs/README_DOCS.md`,
  - `docs/troubleshooting/*`,
  - `SERVER_DEPLOYMENT.md`.
- Script migration/flush:
  - `scripts/migrate_sqlite_to_mysql.py`,
  - `scripts/migrate_mysql_to_sqlite.py`,
  - `scripts/flush_db.py`,
  - dipakai bila maintenance/manual operation.

## Integrasi Keamanan/Layanan Pendukung

- `SESSION_COOKIE_*` defaults dari config.
- CSRF enforcement pada route sensitif.
- Import dari `infrastructure/dialect_upsert.py` memastikan upsert sesuai dialect.
- Upload rate limiting (`UPLOAD_RATE_LIMIT_MAX_REQUESTS`, `UPLOAD_RATE_LIMIT_WINDOW_SECONDS`) untuk endpoint unggah.

