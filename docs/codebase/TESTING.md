# Testing Strategy & Coverage Snapshot

## Tujuan Testing

- Menjamin stabilitas alur unggah + manual + preview.
- Memastikan query/filter/export konsisten.
- Menjaga analisis periode dan workbook export tetap valid.
- Mempertahankan keamanan dasar input dan CSRF/CSRF-adjacent flows.

## Unit / Functional Test Suite

- `tests/test_app_factory.py`
- `tests/test_models.py`
- `tests/test_routes.py`
- `tests/test_queries_sqlalchemy.py`
- `tests/test_upload_flow.py`
- `tests/test_dataset_long_parse.py`
- `tests/test_upload_preview.py`
- `tests/test_data_management_actions.py`
- `tests/test_mutations_sqlalchemy.py`
- `tests/test_period_comparisons.py`
- `tests/test_performance_smoke.py`

## E2E / UI / Browser

- `tests/e2e/smoke.spec.ts`
- `tests/simple_tests/ui_tests/*.spec.js`
- `tests/simple_tests/ui_tests/*.py`
- Playwright CLI di `package.json`:
  - `npm run test:e2e`
  - `npm run test:e2e:ui`
  - `npm run test:e2e:install`

## Dokumen Testing Eksisting

- `tests/README.md` (overview)
- `tests/README_TESTING.md` (laporan lengkap)
- `tests/TESTING_SUMMARY.md` (ringkasan hasil dan risiko)

## Command Set

- Semua unit: `python -m pytest tests/ -v`
- Coverage dasar: `python -m pytest tests/ --cov=app --cov=models --cov=services --cov-report=term-missing`
- Test spesifik:
  - `python -m pytest tests/test_upload_flow.py -v`
  - `python -m pytest tests/test_upload_template_route.py -v`
  - `python -m pytest tests/test_dataset_catalog.py -v`
- Integrasi dialek remote: `python -m pytest tests/integration/test_remote_dialect_smoke.py -v` (memerlukan DB non-SQLite + migrasi).
- E2E:
  - `cd` root, `npm run test:e2e`

## Status Terkini (Berdasarkan Dokumentasi)

- Ringkasan di dokumen testing menunjukkan cakupan besar dengan beberapa ketidaksempurnaan historis.
- Ada indikasi skor partial pada periode tertentu (mis. 22/35 atau 75% pass) dan catatan bug kritikal lama dalam dokumen ringkas.
- Data ini bisa stale; jika perlu, jalankan suite baseline setelah setiap patch besar untuk status yang valid saat ini.

## Focus Test Baru (yang perlu dipertahankan)

- Upload parser tolerance untuk `quarterly`/`yearly` marker.
- Duplicate candidate warning vs actual overwrite path.
- Template dataset-aware generation/download.
- Filter period range dan status filter persistence across export + analysis.
- File lock handling di Windows (`WinError 32`) saat delete preview file.

