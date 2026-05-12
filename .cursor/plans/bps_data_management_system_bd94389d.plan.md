---
name: BPS Data Management System
overview: A simple Python-based system for BPS data management with Excel upload or manual input, landing page repository metrics, and data management dashboard.
todos:
  - id: setup-flask-app
    content: Create basic Flask app with landing page + upload, manual input, and dashboard routes
    status: completed
  - id: design-database-schema
    content: Design SQLite schema that stores uploader metadata, versioning, and normalized time breakdowns
    status: completed
  - id: implement-excel-parser
    content: Build Excel parser that handles both horizontal and vertical layouts (upload path only)
    status: completed
  - id: create-data-normalizer
    content: Normalize varied Excel layouts and manual form data into a single record shape
    status: completed
  - id: build-input-metadata
    content: Capture uploader name + versioning for every upload or manual input
    status: completed
  - id: implement-data-aggregation
    content: Implement pre-aggregation engine that feeds landing page and dashboard summaries
    status: completed
    notes: Fitur ini telah dinonaktifkan pada fase cleanup agar aplikasi fokus sebagai repository data.
  - id: build-dashboard-ui
    content: Make dashboard with filters (periode, tipe data, uploader, versi) plus metrik ringkas repositori
    status: completed
  - id: add-validation-layer
    content: Add validation and error handling for both upload and manual input flows
    status: completed
  - id: add-upload-preview-confirmation
    content: Add two-step Excel upload with parser preview, duplicate candidate detection, and explicit confirmation before insert
    status: completed
  - id: add-upload-duplicate-skip-option
    content: Add upload confirmation option to skip duplicate rows per candidate row and avoid overwriting existing records
    status: completed
  - id: add-upload-duplicate-overwrite-option
    content: Change duplicate-confirmation behavior to overwrite existing rows (UPSERT) for unchecked candidates and tighten overwrite warnings
    status: completed
  - id: unify-upload-manual-duplicate-key
    content: Align upload duplicate detection with manual input by using indicator + period key (indicator_name, year, month, quarter) for early conflict warnings.
    status: completed
  - id: add-manual-duplicate-early-detection
    content: Add early duplicate detection on manual input using indicator + period key (indicator_name, year, month, quarter) and show confirmation warning before save.
    status: completed
  - id: relax-manual-period-parser
    content: Izinkan parsing periode manual yang toleran (Triwulanan menerima YYYY-MM, Tahunan menerima YYYY-MM sebagai penanda) supaya tidak ada penolakan format period_date.
    status: completed
  - id: retain-quarterly-yearly-month-marker
    content: Pertahankan `month` pada path marker `YYYY-MM` untuk `quarterly` dan `yearly` agar penyimpanan dan tampilan ikut `YYYY-MM` bila marker eksplisit dipakai.
    status: completed
  - id: add-upload-template-download
    content: Add default single-sheet Excel template and expose download link from /upload form
    status: completed
  - id: add-upload-template-dual-sheet
    content: Add dual-sheet template with horizontal and vertical examples plus per-sheet instructions in the downloadable workbook
    status: completed
  - id: implement-export-feature
    content: Provide CSV/Excel export from dashboard/repository views
    status: completed
  - id: add-period-range-filter
    content: Add start/end period date-range filters on Preview-Data, Data-Management, and Dashboard pages
    status: completed
  - id: python-modular-refactor
    content: Modularize Python — config.py, services/ package, slim app.py, models get_distinct_years, test DB helpers
    status: completed
  - id: aggregation-wsgi-config
    content: services/aggregation, aggregator shim, configure_flask_app, wsgi.py entrypoint
    status: completed
    notes: Komponen agregasi ini sudah dibersihkan pada fase remove-aggregated-summary-feature; rute/servis agregat tidak lagi aktif.
  - id: app-factory-routes-crud-tests
    content: create_app + routes/ register_routes, data_management_actions service, regression + perf smoke tests
    status: completed
  - id: utc-listview-sql-dry
    content: timeutil UTC helpers, list_view pagination/filters, models filter-clause DRY
    status: completed
  - id: secret-and-db-errors
    content: production secret warnings + REQUIRE_FLASK_SECRET; models CRUD sqlite3/logging
    status: completed
  - id: ci-pinned-requirements
    content: Pin requirements.txt + requirements-dev.txt; GitHub Actions pytest (3.11–3.13)
    status: completed
  - id: models-package-split
    content: Split models.py into models/ package; DB_PATH + SQLAlchemy engine for tests
    status: completed
  - id: upload-preview-disk-sessions
    content: Disk-backed upload preview sessions under UPLOAD_FOLDER for multi-worker
    status: completed
  - id: upload-flow-module-stub
    content: services/upload_flow.py stub (constants + upload_folder_from_config); further route extraction optional
    status: completed
  - id: upload-flow-extract-routes
    content: upload_flow process_upload_confirm/post_file/manual + thin upload_routes; gitignore _preview_sessions
    status: completed
  - id: upload-flow-unit-tests
    content: tests/test_upload_flow.py — mocks for preview/cache + db_path for confirm/manual inserts
    status: completed
  - id: excel-parser-public-api
    content: excel_parser/api.py stable facade; package __all__ without underscore exports
    status: completed
  - id: entry-list-page-facade
    content: services/entry_list_page.py DRY preview + data-management + export filters
    status: completed
  - id: models-session-kwarg-seam
    content: Optional SQLAlchemy session on queries/mutations/browse + write_session in infrastructure/db
    status: completed
  - id: upload-parse-commit-modules
    content: Phase A strangler — services/upload_parse.py + upload_commit.py; persist dari handlers; tests/test_upload_parse.py
    status: completed
  - id: playwright-cli-smoke-script
    content: scripts/playwright_cli_smoke.ps1 + .gitignore .playwright-cli; npx @playwright/cli
    status: completed
  - id: backend-tests-excel-upload-dup
    content: test_excel_parser.py + upload_flow duplicate confirm branches
    status: completed
  - id: gh-issues-65-70-testing-factory-upload-entrylist
    content: "GitHub #65–#70: functional pytest.ini [pytest], TESTING.md canonical smoke + env notes, upload_response_adapter + tests, application/factory.py + slim app.py, services/entry_list facade + route test, upload audit txn doc."
    status: completed
  - id: gh-issues-72-76-upload-seams-period-dataset
    content: "GitHub #72–#76: upload_intake_finalize orchestration; upload_preview_session_storage Protocol; upload_request_policy CSRF+rate limit; data_entries_period_marker_range_from_request; dataset_intake.resolve_dataset_for_intake + tests."
    status: completed
  - id: playwright-test-pom-ci
    content: Root package.json, playwright.config webServer, e2e POM, CI e2e job
    status: completed
  - id: docs-agents-overview-pyfiles
    content: Sync metadata/AGENTS.md, OVERVIEW.md, PY_FILES.md to models/ routes services
    status: completed
  - id: excel-parser-package-split
    content: excel_parser/ package (normalize, layout, records, parse_layouts, payload); remove excel_parser.py
    status: completed
  - id: period-analysis-workbook-split
    content: services/period_analysis_workbook.py (OpenPyXL); period_analysis_export.py thin HTTP wrapper
    status: completed
  - id: upload-preview-source-helper
    content: excel_preview_source_from_payload in upload_preview; DRY upload_flow + build_upload_preview
    status: completed
  - id: upload-preview-session-refactor
    content: Refactor services/upload_preview.py session I/O, duplicate lookup helpers, and context builders to keep preview behavior stable.
    status: completed
  - id: upload-preview-sample-limit-fix
    content: Ensure upload preview sample rows are visible by defaulting upload parse to PREVIEW_SAMPLE_LIMIT so `entries_preview` is populated.
    status: completed
  - id: period-analysis-workbook-refactor
    content: Refactor services/period_analysis_workbook.py into sheet-level helpers (`_build_dashboard_sheet`, `_build_comparison_sheet`, `_build_ytd_sheet`, `_build_metadata_sheet`) with orchestrator `build_period_analysis_workbook`.
    status: completed
  - id: period-comparison-calculators-split
    content: period_comparison_calculators.py pure math + helper math (`_safe_divide`, `_calc_growth`, `_calc_percentage`) and regression checks in `tests/test_period_comparisons.py`.
    status: completed
  - id: mutations-refactor
    content: Refactor models/mutations.py transaction logic and add shared mutation helpers before full regression of insert/delete/update paths.
    status: completed
  - id: upload-security-hardening
    content: Add CSRF token enforcement on upload POST, secure session cookie defaults, and upload endpoint rate limiting.
    notes: Updated limiter identity to use a session-bound `_upload_client_id` key to prevent cross-session bleed while preserving per-session abuse prevention.
    status: completed
  - id: e2e-upload-preview-filepicker
    content: Add Playwright E2E coverage for upload file picker + preview summary panel + preview-data page reachability.
    status: completed
  - id: cleanup-tmp-directory
    content: Ensure local temporary folder tmp/ is gitignored and removed from repository tracking.
    status: completed
  - id: improve-upload-duplicate-alert-message
    content: Clarify upload duplicate conflict alerting/warnings by referencing unique key scope (uploader, version, indicator, period) and explicit user actions.
    status: completed
  - id: detect-internal-upload-duplicate-rows
    content: Detect and block duplicate indicator+period rows inside the uploaded file before database insert/confirm, with clearer user-facing validation feedback.
    status: completed
  - id: make-universal-parser-time-period-aware
    content: Make universal Excel period parser respect time_period (monthly/quarterly/yearly) to avoid malformed/serial-based period misparsing.
    status: completed
  - id: prd-53-universal-template-slices-54-56
    content: "PRD-53 (GitHub #54–#56): dataset `universal`, `template_universal.xlsx`, long-row parse + flexible period, upload form tanpa picker BI, tes + docs/prd/."
    status: completed
  - id: prd-53-issue-58-playwright-universal-upload-smoke
    content: "GitHub #58: Playwright smoke universal template → pratinjau; fixture static/e2e_universal_template.xlsx; playwright.config testDir tests/e2e."
    status: completed
  - id: make-period-display-period-aware
    content: Make display of saved periods in data-management, preview-data, and upload sample table period-aware for monthly/quarterly/yearly (YYYY-MM, YYYY-Qn, YYYY).
    status: completed
  - id: sqlalchemy-mysql-refactor-plan
    content: "SQLAlchemy 2.0 (GitHub #9): Task 12 selesai — `models/` tanpa `get_conn`/raw sqlite3 persistence; `temp_db_path` function-scoped di simple_tests agar tes manual tidak berbagi DB dengan `populated_db`; suite `pytest tests --ignore=tests/integration` hijau. Detail: docs/superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md"
    status: completed
  - id: dotenv-env-files
    content: "python-dotenv + `.env.example`; `config` loads `.env` and optional `DOTENV_PATH` with override=False; `.gitignore` `.env`/`.env.local`; README env table."
    status: completed
  - id: pr10-merge-requirements-dev
    content: "GitHub PR #10 merged to main; conflict `requirements-dev.txt` resolved (beautifulsoup4 + psycopg); branch chore/remove-github-folder deleted."
    status: completed
  - id: remove-github-folder-from-repo
    content: "Removed `.github/` (workflows) from repo local+remote; README/planning/docs updated for manual pytest + integration smoke."
    status: completed
  - id: add-server-deployment-doc
    content: "Add SERVER_DEPLOYMENT.md: deployment via Webmin/Git, MySQL initialization, Alembic migration, SQLite-to-MySQL migration, Gunicorn/systemd, and runbook checklist."
    status: completed
  - id: remove-aggregated-summary-feature
    content: Remove /aggregated page and pre-aggregation feature stack (services/aggregation, summary_store, aggregator shim, templates, and DB table dependencies) so the app remains data repository focused.
    status: completed
  - id: auto-upload-time-version
    content: Auto-fill upload/manual input metadata with WITA timestamp at submit time (backend-only), remove manual "Waktu Unggah" input, and show upload time in WITA on preview/data-management/landing.
    status: completed
  - id: add-db-flush-multi-target-script
    content: Add `scripts/flush_db.py` to clear `data_entries` rows for SQLite and/or MySQL with target selector (`sqlite/mysql/both`), defaulting to interactive startup with preflight URL/file/table checks; preloads `.env`/`DOTENV_PATH`, and supports fallback to `config.database_url()` when explicit MySQL URL env vars are missing, plus `--dry-run` and non-interactive `--targets` + `--yes` for hosting.
    status: completed
  - id: add-mysql-to-sqlite-backup-script
    content: Add `scripts/migrate_mysql_to_sqlite.py` for one-way backup of `data_entries` from SQLAlchemy source DB (MySQL/PostgreSQL defaulting to env-sourced URLs) into SQLite file, with optional truncate/append mode and verification checks.
    status: completed
  - id: refactor-upload-input-dataset-catalog
    content: Refactor upload/manual flow into dataset-aware workflow with sheet selection (exclude Resume, PMSE, Perkembangan Indikator) and per-dataset template generation.
    notes: "Fase 0–6 (2026-04-16): long-parse + sheet title + `test_dataset_long_parse`; dok terpusat `docs/README_DOCS.md` (unggah/migrasi/changelog); smoke `scripts/agent_browser_upload_smoke.ps1`. Legacy: nonaktif via `REQUIRE_DATASET_FOR_UPLOAD=1` di server. UX: satu tombol Unduh Template Excel setelah pilih dataset (`_upload_form` + `dataset_template_urls_json`). MySQL skema: `docs/troubleshooting/mysql-schema-dataset-code-and-alembic.md` + `scripts/apply_dataset_code_migration.py` (stamp `002_dataset` bila skema lengkap tapi `alembic_version` tertinggal; `upgrade head` bila `upload_runs` belum ada). Windows unggah WinError 32: `docs/troubleshooting/windows-upload-winerror-32.md` + `excel_parser/payload.py` tutup `ExcelFile` dengan `with`."
    status: completed
  - id: add-upload-runs-audit
    content: Add `upload_runs` audit logging for upload provenance (dataset, source sheet, hash, row counts, duplicate count, status, error summary) and dataset-aware uniqueness semantics.
    notes: "Growth metrics (M2M/Q2Q/Y2Y) stored as metric dimension, partial rows logged as warnings, and template download requires dataset selection first. Implementasi (2026-04-16): ORM `UploadRun`, migrasi 002, `services/upload_runs.record_upload_run` dipanggil dari alur upload sukses/konfirmasi."
    status: completed
  - id: dataset-template-spec-and-form-generation
    content: Define dataset-specific template schemas from REKAP sheet analysis and generate `.xlsx` templates dynamically per selected dataset.
    notes: "Fase 1: `services/dataset_catalog.py` + `services/template_service.py` + `static/templates/rekap_dataset_long_templates.xlsx` (`scripts/build_rekap_long_templates.py`). Fase 0–2 (2026-04-16): matriks `docs/superpowers/contracts/2026-04-16-dataset-matrix.md`; `GET /upload/template/<dataset_slug>`; injeksi katalog ke `upload_routes` + partials upload/manual; env `REQUIRE_DATASET_FOR_UPLOAD`."
    status: completed
  - id: parser-manual-dataset-context
    content: Extend upload/manual parser and validation paths to require dataset context and enforce dataset-specific header contracts.
    notes: "Fase 3–4 (2026-04-16): `dataset_code` pada baris (`upload_flow`, `manual_entries`, `dialect_upsert`); duplikat + preview aware dataset; filter list UI. Header contract ketat per dataset masih item Fase 5."
    status: completed
  - id: dead-code-removal-chart-analysis
    content: "Remove dead chart/analysis artifacts: charts.py, fetch_series_for_comparison, plotly dep, dead CSS selectors, stale docs. Issues #35-38 closed."
    status: completed
    notes: "PR #45 merged into main. Issues #35-38 closed 2026-05-06."
  - id: dead-code-removal-float-imports
    content: "Consolidate _to_float, remove app.py test aliases, clean import noise. Issues #41-43."
    status: completed
    notes: "Part of dead code sweep 2026-05-06. Issues #41, #42, #43 closed."
  - id: prd-006-test-reliability-period-architecture
    content: "PRD 006 — pytest bootstrap vs .env, semantik periode triwulanan (tahun polos), tes dashboard berbasis makna kolom, seam error integritas & kebijakan unggah, rapatkan API parser, sinkron docs/plan. Lihat docs/plans/issues/006-prd-test-reliability-period-semantics-architecture.md"
    status: completed
    notes: "PR #52 merged ke main (2026-05-06); #48–#51 closed. Item PRD lanjutan (seam error integritas unggah, permukaan publik parser, DRY period marker) belum dieksekusi — lihat isi PRD 006 bila dilanjut."
  - id: pytest-upload-runs-manual-and-confirm
    content: "Pytest asserts `upload_runs` after successful `process_manual_input_post` (#62) and `process_upload_confirm` (#63); `tests/test_upload_flow.py`."
    status: completed
isProject: false
---

File ini berada di **`.cursor/plans/`** dalam repo (ikut Git + path yang sama dipakai Cursor). Buka proyek dari clone workspace: path relatif `.cursor/plans/bps_data_management_system_bd94389d.plan.md`. Salinan di luar repo (`%USERPROFILE%\.cursor\plans\…`) hanya perlu disamakan bila kamu mengedit plan di luar folder proyek.

# BPS Data Management System Architecture

## System Overview

A lightweight Flask system where data can enter via Upload Excel or Manual Input, landing page shows repository-level overview metrics, and dashboard renders stored data entries. **Persistence:** SQLAlchemy 2.0 dengan **`DATABASE_URL`** (SQLite file default dev, MySQL/PostgreSQL di produksi) — `docs/superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md`.

## Data Input Workflow

### Dua Opsi Masuk Data

| Opsi             | Keterangan                      | Format Detection                         |
| ---------------- | ------------------------------- | ---------------------------------------- |
| **Upload**       | User mengunggah file Excel      | Ya — deteksi layout horizontal/vertikal  |
| **Input Manual** | User mengisi form/data langsung | Tidak — data sudah terstruktur dari form |

### Metadata Wajib (Upload & Input Manual)

Setiap upload/input harus menyertakan:

- **Pengupload**: Nama orang yang mengunggah atau menginput data.
- **Waktu unggah**: Sistem sekarang mengisi `version` dengan timestamp backend WITA saat unggah/input manual, lalu diperlakukan sebagai identitas versi untuk mencegah duplikasi dan melacak revisi.

Versioning dipakai untuk:

- Mencegah duplikasi bila ada kesalahan upload/input.
- Melacak riwayat revisi data.

## Landing Page & Navigation

- **Landing page**: entry point dengan metrik overview repository (jumlah baris data terbaru, indikator aktif, dan metadata unggahan terakhir).
- Terdapat tombol utama: Upload dan Manual Input.

## Core Components

### 0. Application layout (refactored)

- **`config.py`**: `BASE_DIR`, allowed sets, upload limits, `resolve_secret_key()`, `configure_flask_app(app, testing=...)`, `default_secret_risk_in_production`, opsional `REQUIRE_FLASK_SECRET` / peringatan jika `FLASK_ENV=production` dengan secret default (ditekan saat pytest memuat app).
- **`services/`**: `validation`, `upload_preview` (pratinjau + sesi disk `_preview_sessions` + `excel_preview_source_from_payload`), `upload_flow` (form/validasi/simpan file, konfirmasi pratinjau, respons terstruktur untuk route; `cache_upload_preview` tetap memakai Flask `session`), `request_params`, `manual_entries`, `charts`, `raw_export`, `period_analysis_workbook` (OpenPyXL multi-sheet), `period_analysis_export` (form + Flask `Response`), `period_filters`, `period_comparison_calculators` (murni), `period_comparisons` (SQL + orkestrasi), `data_management_actions`, `timeutil` (UTC ISO / timestamp), `list_view` (pagination + kwargs query + dict filter UI untuk preview/data-management).
- **`routes/`**: `register_routes(app)` mendaftarkan view lewat `add_url_rule` (endpoint sama dengan sebelum refactor). `pages.py` (landing, preview, export, plot JSON), `upload_routes.py` (upload + manual, memakai `current_app.config`), `manage.py` (data management + export period analysis).
- **`application/factory.py`**: `create_app(testing=..., init_sqlalchemy=...)` dengan `Flask(..., root_path=<repo root>)` agar `templates/` tetap ditemukan. **`app.py`**: modul tipis — `app = create_app(...)` + re-export `create_app`, `allowed_file`, `validate_metadata` untuk kompatibilitas impor tes / skrip. **`wsgi.py`**: `from app import app` untuk server produksi.
- **`models/`** (paket): `connection` (`DB_PATH`, `init_db` pada engine SQLAlchemy), `queries`, `mutations`, `browse`, `data_filters`; re-export API publik + analitik periode dari `services.period_comparisons`. Monolit `models.py` dihapus.

### 1. Data Input & Processing Pipeline

- **Upload**: Excel → Layout Detection (+ opsi override) → Parse payload (diagnostics) → Normalize → Metadata (uploader + version) → Validate → Konfirmasi sebelum simpan.
- **Manual Input**: Form → Normalize → Metadata → Validate → Store.
- **Excel Parser**: `pandas` + `openpyxl`, detect layout (horizontal vs vertical).
- **Normalization**: Samakan ke schema tunggal meskipun sumber berbeda.
- **Validation**: Cek tipe data, periode, dan metadata.

### 2. Database Schema Design

```
data_entries (
    id,
    uploader_name,
    version,
    template_type,
    data_type (flow/stock),
    time_period (monthly/quarterly/yearly),
    indicator_name,
    value,
    unit,
    region_code,
    year,
    month (NULL for non-monthly),
    quarter (NULL for non-quarterly),
    created_at
)
```

### 3. Dashboard Module

- **Visualization**: Tabel + metrik ringkas repository.
- **Filters**: Periode (bulanan/triwulanan/tahunan), data type, uploader, version.
- **Export**: CSV/Excel downloads.
- **Repository Quick Metrics**: Menampilkan jumlah baris, indikator aktif, dan rentang periode.

### 4. Data Management Focus

- **Data Focus**: Menekankan penyimpanan data dan operasi CRUD; ringkasan ringkas diturunkan langsung dari data aktif.

## Excel Template Handling (Upload-only)

### Template Format Detection

Parser sekarang memakai alur deteksi dua lapis:

- Deteksi awal otomatis untuk `layout` (vertical/horizontal) dengan `layout_override` opsional.
- Fallback ke `detect_template_format` bila materialisasi data gagal.
- `parse_excel_payload` menyertakan hasil deteksi (`layout`, `header_row`, mode parse, warnings, invalid rows) untuk dipakai pada mode pratinjau.

### Data Extraction Patterns

- **Vertical**: Periode di kolom pertama.
- **Horizontal**: Periode di header.
- **Mixed**: Strategi parsing adaptif.

## Technology Stack

- **Backend**: Flask
- **Database**: SQLite
- **Excel Processing**: pandas + openpyxl
- **Frontend**: Jinja2 + HTML sederhana (Bootstrap opsional)
- **Charts**: Chart.js (opsional)

## Data Flow Architecture

```mermaid
graph TD
    A[Landing Page] --> B{Action}
    B -->|Upload| C[Upload File Excel]
    B -->|Manual| D[Form Input Manual]
    B -->|Lihat Metrik| P[Ringkasan Repositori]
    C --> E[Format Detection + Override]
    E --> F{Layout?}
    F -->|Vertical| G[Parse Vertical]
    F -->|Horizontal| H[Parse Horizontal]
    G --> I[Normalize Data]
    H --> I
    D --> J[Normalize Data]
    I --> K[Input Metadata]
    J --> K
    K --> L[Pengupload + Versioning]
    L --> M[Validate & Clean + Duplicate Check]
    M --> N{Konfirmasi User}
    N -->|Tolak| C
    N -->|Setuju| O[Store to SQLite]
    O --> N2[Dashboard Display]
```

Ringkasan:

- **Upload**: Excel → Layout Detection (+override optional) → Parse payload + duplicate scan → User Confirmation (+opsi lewati duplikasi) → DB → Dashboard.
- **Manual**: Form → Normalize → Metadata → Validate → DB → Dashboard.
- **Landing Page**: Menampilkan metrik repositori + metadata terakhir, aksi menuju Upload/Manual.

## Implementation Phases

1. **Phase 1** (done): Setup Flask + landing page (repository metrics) dan capture metadata (pengupload, version).
2. **Phase 2**: Implement upload + manual input endpoints, parsing, normalization, validation.
3. **Phase 3**: Schema DB dengan metadata + normalized fields.
4. **Phase 4** (done): Bangun dashboard card metrik ringkas tanpa engine agregasi terpisah.
5. **Phase 5** (done): Dashboard UI dengan filter/periode + ringkasan repo.
6. **Phase 6** (done): Export functionality + validation/error feedback.

## Work Completed

- Flask shell with routes (`landing_page`, `upload_data`, `manual_input`, `dashboard`, `data_management`, `generate-period-analysis`) plus flash messaging.
- Template set now targets `base.html`, `landing.html`, `upload.html`, `dashboard.html`, `data_management.html` and CSS skeleton added.
- Directories `templates/`, `static/css/`, and `uploads/` created; `requirements.txt` tracks dependencies.
- Repository-level storage and query paths now drive dashboard metrics; per-data insert recalculation uses live aggregates (no separate summary cache).
- Dashboard UI now exposes filter controls and a data table that reports the persisted entries.
- Metadata validation enforces allowed `data_type`/`time_period` before persistence.
- Export route streams raw CSV/Excel from current filtered dataset.
- SQLite schema + insert helpers ready for uploader/version metadata and normalized time breakdowns.
- Excel parser + manual normalization written so both flows reuse the same persistence path.
- **Bulk operations implemented**: Added checkbox selection, bulk delete, and bulk update functionality in data management page for efficient multi-record operations.
- **Period comparison analysis implemented**: Added Q to Q, M to M, Y to Y, YTD, and C to C analysis with interactive pivot tables for indicator analysis.
- **Data management pagination implemented**: Added configurable rows per page (5, 10, 15, 20, 30, 50, 100) with persistent checkbox state across page changes.
- **UI/UX refactor completed**: Refactor visual shell, navigasi, komponen inti, dan sistem status/feedback untuk desain lebih opinionated (typografi bold, badge aksen, micro-interaksi, dan aksesibilitas terarah).
- **Preview data pagination implemented**: Added configurable rows per page (5, 10, 15, 20, 30, 50, 100) with full pagination controls.
- **Table UI consistency implemented**: Harmonized Data-Management and Preview-Data table visuals using shared table classes and metadata badge components, while keeping Data-Management actions and bulk tools unchanged.
- **Bulk operations implemented**: Added checkbox selection, bulk delete, and bulk update functionality in data management page for efficient multi-record operations.
- **Date-range filtering implemented**: Added `start_period`/`end_period` filters across Preview-Data, Data-Management, and Dashboard pages with SQL-layer filtering and URL/payload propagation to exports and analyses.
- **Value-range filtering implemented**: Added `value_min`/`value_max` filters on Preview-Data and Data-Management, including backend query propagation, pagination consistency, export filtering, and filter-based bulk delete behavior.
- **Upload preview + confirm flow implemented**: Upload now stores temporary preview state, memuat ringkasan parser (layout/source row/warnings/sample/invalid rows), menampilkan kandidat duplikasi, dan hanya menyimpan setelah user mengonfirmasi; state pratinjau disimpan di disk di bawah `UPLOAD_FOLDER` agar beberapa worker/process berbagi sesi yang sama.
- **Upload duplicate-skip option implemented**: Konfirmasi upload kini menyediakan checkbox per kandidat duplikasi, tombol kontrol cepat `Pilih Semua`, `Batal Semua`, dan `Balik Pilihan`, serta ringkasan jumlah kandidat yang dipilih untuk dikecualikan; notifikasi upload sekarang ditata agar tetap stabil di bagian atas halaman dengan lebar terbatas dan teks tidak menumpuk layout.
- **Upload duplicate preview refinement**: Baris pada `Kandidat Duplikasi` kini menampilkan nilai (Nilai) agar format sejalan dengan `Contoh data yang akan disimpan`, sambil mempertahankan checkbox per baris untuk pengecualian duplikasi.
- **Upload preview sample consistency implemented**: `parse_and_validate_upload_payload` sekarang menggunakan `PREVIEW_SAMPLE_LIMIT` sebagai default agar `sample` pada `parse_excel_payload` tidak kosong saat pratinjau upload, sehingga baris yang ditampilkan pada ringkasan pratinjau konsisten dengan total baris yang diproses.
- **Verification milestone Gate-3 complete**: `tests/simple_tests/functional_tests` dan `tests/simple_tests/bug_tests` sudah diverifikasi ulang; celah keamanan upload ditutup dengan CSRF token, session HttpOnly, dan rate limiting, kemudian diuji pada alur keamanan.

## Project Rule

- Changes to code/features must be accompanied by updates to `docs/README_DOCS.md` (changelog), `docs/planning.md` (stub checklist if needed), and **`.cursor/plans/bps_data_management_system_bd94389d.plan.md`** (YAML todos), enforced by `.cursor/rules/planning-&-executing-sync.mdc`.

## Key Challenges & Solutions

### Excel Format Variability (Upload saja)

- Parser fleksibel + deteksi layout; manual input skip format detection.

### Versioning & Dobel Upload

- Field `version` + rules (unik per batch atau per uploader+timestamp).

### Time Period & Data Type

- Normalisasi `year/month/quarter`, field `data_type` dari form/metadata.

### Repository Data Focus

- Statistik singkat dihitung dari data aktif (ringkas) setelah `Store to SQLite`, tanpa cache agregasi terpisah.

## File Structure

```
bps_data_system/
├── app.py                 # Flask app instance + compat re-exports (factory in application/)
├── application/           # create_app factory (root_path = repo root)
├── models/                # Paket SQLite (connection, queries, mutations, browse, …)
├── excel_parser.py        # Excel logic (upload-only)
├── templates/
│   ├── landing.html       # Landing page with repository metrics + metadata
│   ├── upload.html        # Form upload + manual input metadata
│   ├── dashboard.html
│   └── base.html
├── static/
│   ├── css/
│   └── js/
├── data.db
└── uploads/
```

## Documentation Update
- Added OVERVIEW.md under project root as a concise module/folder onboarding reference for contributors and agents (root scope, assets/templates/static, and key Python modules).

- **Docs Update:** OVERVIEW.md expanded with per-folder summaries for assets/static/templates dan ringkasan modul Python inti (app.py, excel_parser.py, models.py).
- [x] Buat dokumentasi detail per-folder: `assets/README.md`, `static/README.md`, `templates/README.md`, `templates/partials/README.md`.
- [x] Buat dokumentasi gabungan untuk semua berkas Python di `PY_FILES.md`.
- [x] Sinkronisasi pembaruan dokumentasi ke `docs/README_DOCS.md`, `docs/planning.md`, dan `.cursor/plans/bps_data_management_system_bd94389d.plan.md`.

## Recent Backend & Upload UX Updates

- Centralized period parsing logic into a new shared utility module `periods.py` (`parse_period_date`), now used by both `app.py` (manual input builder) and `models` (`insert_single_entry`). This removes duplicate implementations of `_parse_period_date` and keeps `period_date` handling consistent across manual and CRUD flows.
- Refined upload UX:
  - Global flash/alert component repositioned to sit below the navbar and above the page header, preventing overlapping with the Upload form or preview panel.
  - JavaScript for duplicate-candidate selection on upload preview extracted into `templates/partials/_script_upload_duplicates.html` so that `upload.html` focuses on structure while behavior lives in a dedicated partial.
- Upload refactor tracking (riwayat di git: `docs/refactor-planning.md` hingga 2026-04-17): `services/upload_flow.py` — `persist_upload_entries`, `build_upload_response`, orchestrator confirm/post-file.
- Refactor progress: `services/upload_flow.py` — helper orchestrator untuk `process_upload_confirm` (narasi panjang → `docs/README_DOCS.md` + plan SQLAlchemy).

- **Upload UX update:** 	emplates/partials/_upload_form.html kini menyediakan tombol **Unduh Template Excel** (mengarah ke static/templates/upload_template.xlsx) dan catatan format parser untuk upload yang lebih jelas.

## Update terbaru (2026-04-13)
- Iterasi lanjut menguatkan alur unggah/manual berikut preview/duplikasi dan update tampilan:
  - Rute unggah dan kontrol manual (`routes/upload_routes.py`, `templates/partials/_manual_form.html`, `templates/upload.html`).
  - Layanan unggah & pratinjau (`services/upload_flow.py`, `services/upload_preview.py`) untuk flow duplikasi lebih konsisten.
  - Penyesuaian model/helper + uji regresi (`tests/test_models.py`, `tests/test_mutations_baseline.py`, `tests/test_data_management_actions.py`, `tests/test_upload_flow.py`, `tests/test_upload_preview.py`, `tests/simple_tests/functional_tests/test_manual_entry.py`).
  - Dokumen rencana operasional ditambah di `docs/superpowers/plans/2026-04-13-logging-and-mysql-migration.md`.
