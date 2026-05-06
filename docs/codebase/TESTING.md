# Testing Strategy & Coverage Snapshot

## Tujuan Testing

- Menjamin stabilitas alur unggah + manual + pratinjau data (`preview-data`).
- Memastikan query, filter `period marker`, dan ekspor konsisten.
- Mempertahankan parser Excel (layout horizontal/vertikal, dataset-aware) dan normalisasi periode.
- Menjaga keamanan dasar input dan alur yang berdekatan dengan CSRF pada unggah.

## Default pytest & basis data

- Root `tests/conftest.py` mengatur **`DATABASE_URL`** ke SQLite berkas di repo **sebelum** impor `models`, supaya nilai `DATABASE_URL` dari `.env` (mis. MySQL produksi) tidak memutuskan koleksi tes atau suite default.
- Untuk menjalankan tes **terhadap DSN dari lingkungan** (mis. integrasi MySQL di Docker): set  
  `USE_ENV_DATABASE_URL_FOR_TESTS=1` (atau `true` / `yes` / `on`) **dan** `DATABASE_URL` ke DSN non-sqlite, lalu jalankan subset yang relevan (lihat README root bagian integrasi dialek).

## Unit / functional (cuplikan — lihat `tests/` untuk daftar aktual)

- `tests/test_app_factory.py`, `tests/test_models.py`, `tests/test_routes.py`
- `tests/test_queries_sqlalchemy.py`, `tests/test_mutations_sqlalchemy.py`
- `tests/test_upload_flow.py`, `tests/test_upload_preview.py`, `tests/test_dataset_long_parse.py`
- `tests/test_excel_parser.py`, `tests/test_data_management_actions.py`
- `tests/simple_tests/functional_tests/` (termasuk pratinjau / dashboard)
- `tests/test_bugs.py` — regresi edge case

## Integrasi dialek remote

- `tests/integration/test_remote_dialect_smoke.py` — memerlukan `USE_ENV_DATABASE_URL_FOR_TESTS=1`, `DATABASE_URL` non-sqlite, dan skema `alembic upgrade head` pada target.

## E2E / UI

- `tests/e2e/smoke.spec.ts` (Playwright)
- `tests/simple_tests/ui_tests/` (Python / legacy JS sesuai tree)

Perintah npm: lihat `package.json` (`test:e2e`, dll.).

## Dokumen testing lain

- `tests/README.md` — overview
- `tests/README_TESTING.md`, `tests/TESTING_SUMMARY.md` — laporan historis (bisa stale)

## Command set

- Suite Python utama: `python -m pytest tests -q`
- Integrasi remote (contoh):  
  `USE_ENV_DATABASE_URL_FOR_TESTS=1 DATABASE_URL=mysql+pymysql://... python -m pytest tests/integration/test_remote_dialect_smoke.py -q`
- E2E: dari root, `npm run test:e2e`

## Status & fokus

- Setelah patch besar, jalankan ulang suite baseline; angka historis di dokumen lama tidak dijamin mutakhir.
- Fokus regresi: toleransi periode (`time_period` + parser), duplikat unggah, template dataset-aware, filter rentang periode + ekspor, WinError 32 pada file pratinjau (Windows).
