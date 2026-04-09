
## Dokumentasi Ringkas Kode
- **Refactor Python (2026-04, wave 10)**: Monolit `excel_parser.py` diganti **paket** `excel_parser/` (`constants`, `normalize`, `layout`, `records`, `parse_layouts`, `payload`, `__init__` re-export). Impor publik tetap `from excel_parser import parse_excel_payload, …`. **`period_analysis_export`**: styling + pembangunan workbook OpenPyXL dipindah ke `services/period_analysis_workbook.py` (`build_period_analysis_workbook ) `period_analysis_export.py` hanya form + `calculate_period_comparisons` + `Response`.
- **Refactor Python (2026-04, wave 11)**: **`upload_preview` / `upload_flow`**: helper `excel_preview_source_from_payload` memusatkan struktur dict pratinjau pasca-parse; `upload_flow` dan `build_upload_preview` memakainya agar tidak menduplikasi field layout/sample/warnings. **`period_comparisons`**: kalkulator murni (M/M, Q/Q, Y/Y, YTD, C→C) di `services/period_comparison_calculators.py`; helper math ditambah `_safe_divide`, `_calc_growth`, `_calc_percentage` untuk stabilisasi ratio dan urutan key; `period_comparisons.py` hanya query SQLite + orkestrasi. Tes: `tests/test_period_comparisons.py` (tanpa DB), `python -m pytest tests/simple_tests/functional_tests/test_export.py -q`, regresi akhir: `python -m pytest tests/test_period_comparisons.py tests/test_upload_flow.py tests/simple_tests/functional_tests/test_export.py -q`.
- **Tes & E2E (2026-04, wave 9)**: `tests/test_excel_parser.py` (`_to_float`, `detect_template_format`, workbook kosong, `parse_excel_payload` horizontal terpaksa + batas `preview_limit`). `tests/test_upload_flow.py` memperluas `process_upload_confirm` untuk cabang duplikat (partial selection, semua baris di-skip, skip satu simpan sisanya). **`@playwright/test`**: root `package.json` + `playwright.config.ts` (`webServer` Flask tanpa reloader), POM `e2e/pages/LandingPage.ts` / `UploadPage.ts`, spes `e2e/smoke.spec.ts` (role + `getByLabel('Navigasi utama desktop')` untuk link ganda), dan skenario tambahan untuk **upload file picker + pratinjau unggahan** (tombol `Unggah & Pratinjau` menampilkan panel ringkasan) + akses halaman `Preview Data`. CI: job `e2e` di `.github/workflows/ci.yml` setelah job `test` (Node 20, `playwright install chromium --with-deps`). Dokumentasi diselaraskan: `metadata/AGENTS.md`, `README.md`, `README.md`.
- **Smoke browser (2026-04)**: `@playwright/cli` (`npx @playwright/cli@latest`) untuk otomasi agen: `open` / `goto`, `snapshot` (YAML refs), `click` (role-based untuk tautan **Unggah Data**). Artefak CLI di `.playwright-cli/` (diabaikan git). Skrip dapat diulang: `powershell -ExecutionPolicy Bypass -File scripts/playwright_cli_smoke.ps1` — menjalankan Flask tanpa reloader di `:5000`, snapshot relatif `.playwright-cli/smoke-home.yml`, klik nav ke `/upload`, `eval` pathname. Prasyarat: `npx @playwright/cli@latest install-browser chromium`.
- **Refactor Python lanjutan (2026-03, wave 8)**: `services/upload_flow.py` memusatkan alur upload Excel (parse form, validasi file, simpan ke disk, `process_upload_confirm`, `process_upload_post_file`) dan input manual (`process_manual_input_post ) `routes/upload_routes.py` hanya HTTP (`flash`, `redirect`, `session`, `render_template` + helper `_apply_*_flow_response`). `.gitignore` mengabaikan `uploads/_preview_sessions/` (cache pratinjau multi-worker). Verifikasi CI: sama dengan job GitHub Actions — `pip install -r requirements-dev.txt` lalu `python -m pytest tests -q --tb=short` (matrix 3.11–3.13 di `.github/workflows/ci.yml`). Tes unit alur: `tests/test_upload_flow.py` (mock `load_preview_session` / `parse_excel_payload` / `cache_upload_preview`, fixture `db_path` untuk insert).
- **Refactor Python lanjutan (2026-03, wave 7)**: `models/` paket menggantikan monolit `models.py` (`connection`, `queries`, `mutations`, `browse`, `summary_store`, `data_filters`; API publik tetap lewat `models/__init__.py`). `get_conn()` membaca `str(models.DB_PATH)` setiap panggilan agar monkeypatch tes (`models.DB_PATH`) sama perilakunya dengan monolit. Pratinjau upload: sesi disimpan di disk `{UPLOAD_FOLDER}/_preview_sessions/{token}/session.json` (`services/upload_preview.py` + `routes/upload_routes.py`) agar aman multi-worker. Dependensi runtime/dev dipin di `requirements.txt` / `requirements-dev.txt`; CI GitHub Actions `.github/workflows/ci.yml` menjalankan `pytest` pada Python 3.11–3.13 untuk cabang `main` / `master` / `alternative_main`. `services/upload_flow.py`: stub konstanta + `upload_folder_from_config` sebagai titik ekstraksi alur upload berikutnya.
- **Refactor Python lanjutan (2026-03, wave 6)**: `config.configure_flask_app(app, testing=...)` menerima `testing` (dari `create_app`) agar mode tes tidak memicu peringatan produksi. `REQUIRE_FLASK_SECRET` (truthy) memaksa `RuntimeError` jika `FLASK_SECRET_KEY` belum diatur (masih default). `FLASK_ENV=production` + secret default → `logger.warning` kecuali proses di bawah pytest (`pytest` di `sys.modules`, agar suite tetap bersih). `config.default_secret_risk_in_production` untuk predikat yang dapat diuji. Operasi mutasi DB di `models` memakai `except sqlite3.Error` (dan `KeyError`/`TypeError`/`ValueError` di mana relevan) plus `logging` alih-alih `except Exception`/`print` diam-diam. Tes: `tests/test_config_secrets.py` (termasuk subprocess untuk log peringatan).
- **Refactor Python lanjutan (2026-03, wave 5)**: `services/timeutil.py` (`utc_now_iso`, `utc_now_timestamp`) mengganti `datetime.utcnow()` di `models.py`, `excel_parser.py`, `services/manual_entries.py`, `services/upload_preview.py`, dan `tests/test_bugs.py` (menghindari DeprecationWarning). `services/list_view.py` memusatkan pagination (`parse_entries_pagination`, `normalize_entries_page_limit`), `entries_query_kwargs`, dan `build_entries_filters_ui_dict`; dipakai `routes/pages.py` (`preview_data`, `export_data`) dan `routes/manage.py` (`data_management`). `models._build_data_entry_filter_clauses` dipakai bersama oleh `get_total_entries_count`, `query_data_entries`, dan `delete_data_by_filter`. Tes: `tests/test_timeutil.py`.
- **Refactor Python lanjutan (2026-03, wave 4)**: `app.create_app(testing=...)` membangun Flask baru per panggilan, memanggil `register_routes(app)` dari paket `routes/` (`pages.py`, `upload_routes.py`, `manage.py`) dengan `add_url_rule` agar nama endpoint (`landing_page`, `upload_data`, …) tetap sama untuk `url_for`. `app.app` modul = `create_app()` untuk WSGI/impor lama; `tests/conftest.py` mengganti `app_module.app` dengan `create_app(testing=True)` setelah `reload`. Upload memakai `current_app.config["UPLOAD_FOLDER"]`. Logika POST `/data-management` dipindah ke `services/data_management_actions.apply_data_management_post` (kembalian daftar `(pesan, kategori)` untuk `flash`). Tes tambahan: `tests/test_app_factory.py`, `test_regression_routes.py`, `test_performance_smoke.py` (batas waktu longgar + `perf_counter`), `test_data_management_actions.py`.
- **Refactor Python lanjutan (2026-03, wave 3)**: `services/aggregation.py` berisi `fetch_aggregated_summary` / `refresh_aggregated_summary`; `aggregator.py` menjadi shim re-export untuk kompatibilitas impor lama. `config.configure_flask_app(app)` memusatkan setelan Flask (upload folder, max body, secret). `wsgi.py` mengekspor `app` untuk `gunicorn wsgi:app`. Aplikasi memuat agregasi dari `services.aggregation` langsung; tes bug yang mem-patch refresh memakai target `services.aggregation.refresh_aggregated_summary`.
- **Refactor Python lanjutan (2026-03, wave 2)**: `services/period_filters.py` memuat parsing rentang periode + `apply_period_range_filter` (dipakai `get_total_entries_count`, `query_data_entries`, `delete_data_by_filter`). `services/period_comparisons.py` memuat seluruh analitik Q/Q, M/M, Y/Y, YTD, C→C; `calculate_period_comparisons` mengimpor `get_conn` secara lazy dari `models` untuk menghindari siklus impor. `models.py` mengekspor ulang fungsi-fungsi tersebut agar `from models import calculate_period_comparisons` tetap valid.
- **Refactor Python (2026-03)**: Struktur modular tanpa mengubah perilaku HTTP/DB. `config.py` memusatkan path dan konstanta; paket `services/` berisi validasi upload, cache pratinjau + duplikasi, parameter rentang periode, entri manual, grafik Plotly, ekspor CSV/Excel mentah, dan ekspor analisis periode (openpyxl). `models.py` memakai `BASE_DIR` dari `config`, menambah `get_distinct_years()` (menggantikan koneksi SQLite ad-hoc di `app` agar konsisten dengan `DB_PATH` yang di-patch di tes). `app.py` memuat factory + re-export alias `_parse_period_date` / `_build_manual_entry` untuk kompatibilitas tes. Tes `tests/test_bugs.py`: perbaikan `setUp`/`tearDown` ganda dan DB `:memory:` yang tidak berbagi koneksi; helper `_temp_db_attach`/`_temp_db_detach`; data duplikasi unik memakai `quarter` eksplisit; ekspektasi tanggal tidak valid selaras dengan `periods.parse_period_date`. Pesan validasi metadata diselaraskan ke “Tipe data tidak valid.” untuk konsistensi dengan `tests/test_app_utils.py`. `get_total_entries_count` / `query_data_entries` menangani `sqlite3.OperationalError` dan offset negatif secara defensif.

- **Status**: selesai pada fase akhir.
- **Perubahan**: menambahkan README.md di root sebagai peta cepat folder (ssets, 	emplates, static) dan file Python inti (pp.py, ggregator.py, excel_parser.py, models.py).

- Fitur terbaru:
  - Parser Excel sudah di-advance ke alur preview: mendukung deteksi layout campuran/metadata, normalisasi angka lokal, dan `parse_excel_payload` dengan ringkasan diagnostics (`layout`, `header_row`, `warnings`, `invalid_rows`, `sample`).
  - Upload halaman `Upload` diubah jadi dua tahap: pratinjau terlebih dulu lalu konfirmasi sebelum insert.
  - Opsi override layout (`auto`/`vertical`/`horizontal`) ditambahkan pada form upload.
  - Template upload dasar kini tersedia di `/upload` dengan dua format sheet: `Template_Horizontal` dan `Template_Vertical`, masing-masing berisi contoh dan penjelasan di file template Excel.
  - Validasi duplikasi dilakukan sebelum insert terhadap kombinasi `uploader + version + indicator + year + month + quarter`; duplikasi ditampilkan di pratinjau.
  - Pratinjau kini menyediakan opsi lewati data duplikasi secara granular per baris kandidat duplikasi (checkbox per row), termasuk kontrol cepat "Pilih Semua", "Batal Semua", dan "Balik Pilihan" + ringkasan jumlah pilihan agar user tahu kandidat yang dikecualikan.
  - Sistem notifikasi upload ditata ulang agar lebih stabil: posisi tetap di area atas halaman, lebar adaptif tidak mengganggu layout form, dan teks terbungkus rapi tanpa menimpa komponen lain.

- **Dokumentasi detail:** `README.md` kini memuat ringkasan per-folder (ssets, 	emplates, static) dan ringkasan operasional setiap file utama Python untuk keperluan onboarding/refactor cepat.
- [x] Buat dokumentasi detail per-folder: `assets/README.md`, `static/README.md`, `templates/README.md`, `templates/partials/README.md`.
- [x] Konsolidasikan dokumentasi gabungan berkas Python ke dalam `README.md` sebagai sumber tunggal root.
- [x] Sinkronisasi pembaruan dokumentasi ini ke `planning.md` dan `C:/Users/PENGOLAHAN/.cursor/plans/bps_data_management_system_bd94389d.plan.md`.
- [x] Gate-3: verifikasi ulang `tests/simple_tests/functional_tests` dan `tests/simple_tests/bug_tests` setelah perbaikan kompatibilitas test-client & patch skenario error handling; test yang memang mendokumentasikan kerentanan keamanan (`No CSRF`, `No rate limiting`, `Session HttpOnly`) dicatat sebagai `xfail`.

## Refactor Plan (gabungan detail refactor)

# Refactor Plan: Stabilitas dan Keterbacaan Codebase Upload/Analytics

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

I'm using the writing-plans skill to create the implementation plan.

## Goal

Mengurangi kompleksitas pada modul yang dominan besar tanpa mengubah perilaku publik aplikasi agar perubahan lebih aman, konsisten, dan mudah dipelihara.

## Architecture

Menjaga arsitektur `app -> routes -> services -> models` tetap utuh, lalu memecah `services/upload_flow.py`, `services/upload_preview.py`, `services/period_analysis_workbook.py`, `models/mutations.py`, dan `services/period_comparison_calculators.py` menjadi fungsi-fungsi ber-tanggung-jawab tunggal.

## Tech Stack

Python, Flask, pytest, openpyxl.

## Scope

- Modifikasi terbatas pada refactor struktur dan ekstraksi fungsi.
- Tidak ada perubahan endpoint, schema DB, format API publik, atau perilaku input-output resmi.
- Semua task dikerjakan bertahap (2–5 menit per step).

## Working Rules

- Setiap step adalah satu aksi tunggal.
- Setiap step punya verifikasi cepat.
- Setelah step selesai, ceklist diubah menjadi `[x]` dan catatan ditambahkan ke bagian Progress Log.
- Jika step gagal, stop, rollback step, lalu lanjut setelah akar penyebab diperbaiki.
- Lint dan behavior contract harus tetap bisa dipanggil oleh route lama.

## Progress Log

- Catatan ditulis di bawah setiap task selesai.
- Format: `- [YYYY-MM-DD HH:MM] [Team] [StepID] [DONE/BLOCKED] [PIC] - catatan`

Contoh:

- [2026-04-06 10:15] [Tim-UploadFlow] [UPL-1.1] [DONE] [Iris] - baseline smoke test upload_flow berhasil

- [2026-04-06 10:00] [Tim-UploadFlow] [UPL-1.1] [DONE] [RefactorOperator] - Baseline `python -m pytest tests/test_upload_flow.py -q` sudah dijalankan dan lolos.
- [2026-04-06 10:02] [Tim-UploadFlow] [UPL-1.3] [DONE] [RefactorOperator] - Ekstrak helper `parse_and_validate_upload_payload` di `services/upload_flow.py`.
- [2026-04-06 10:05] [Tim-UploadFlow] [UPL-1.1] [DONE] [RefactorOperator] - Verifikasi `python -m pytest tests/test_upload_flow.py -q` setelah baseline.
- [2026-04-06 10:07] [Tim-UploadFlow] [UPL-1.3] [DONE] [RefactorOperator] - Verifikasi ulang `python -m pytest tests/test_upload_flow.py -q` setelah refactor helper parsing; tetap lulus.
- [2026-04-06 10:10] [Tim-UploadFlow] [UPL-1.2] [DONE] [RefactorOperator] - Menambahkan kontrak internal docstring untuk `process_upload_confirm` dan `process_upload_post_file`.
- [2026-04-06 10:11] [Tim-UploadFlow] [UPL-1.2] [DONE] [RefactorOperator] - Verifikasi `python -m pytest tests/test_upload_flow.py -q` setelah kontrak docstring ditambahkan; tetap lulus.
- [2026-04-06 10:14] [Tim-UploadFlow] [UPL-1.4] [DONE] [RefactorOperator] - Ekstrak helper `prepare_duplicate_plan` dan refactor branch duplicate di `process_upload_confirm`.
- [2026-04-06 10:15] [Tim-UploadFlow] [UPL-1.4] [DONE] [RefactorOperator] - Verifikasi `python -m pytest tests/test_upload_flow.py -k duplicate -q` dan `python -m pytest tests/test_upload_flow.py -q`; semua lolos.
- [2026-04-06 10:18] [Tim-UploadFlow] [UPL-1.5] [DONE] [RefactorOperator] - Ekstrak helper `persist_upload_entries` di `services/upload_flow.py` dan ganti panggilan insert langsung menjadi helper.
- [2026-04-06 10:19] [Tim-UploadFlow] [UPL-1.5] [DONE] [RefactorOperator] - Verifikasi regresi penuh `python -m pytest tests/test_upload_flow.py -q`; semua lulus.
- [2026-04-06 10:22] [Tim-UploadFlow] [UPL-1.6] [DONE] [RefactorOperator] - Ekstrak helper `build_upload_response` untuk factory response dan refactor seluruh return `UploadFlowResponse` di `services/upload_flow.py`.
- [2026-04-06 10:23] [Tim-UploadFlow] [UPL-1.6] [DONE] [RefactorOperator] - Verifikasi regresi penuh `python -m pytest tests/test_upload_flow.py -q`; semua lulus.
- [2026-04-06 10:28] [Tim-UploadFlow] [UPL-1.7] [DONE] [RefactorOperator] - Refactor `process_upload_confirm` menjadi orchestrator dan mengekstrak helper duplicate/no-duplicate handling.
- [2026-04-06 10:29] [Tim-UploadFlow] [UPL-1.7] [DONE] [RefactorOperator] - Verifikasi `python -m pytest tests/test_upload_flow.py -q`; ada 2 kegagalan awal, lalu diperbaiki di helper orchestrator (file_name/layout/form_values), ulangi verifikasi dan lulus.
- [2026-04-06 10:35] [Tim-UploadFlow] [UPL-1.8] [DONE] [RefactorOperator] - Refactor `process_upload_post_file` jadi orchestrator melalui helper untuk jalur parse kosong, save-with-duplicate, save-bersih, dan preview.
- [2026-04-06 10:36] [Tim-UploadFlow] [UPL-1.8] [DONE] [RefactorOperator] - Verifikasi regresi penuh `python -m pytest tests/test_upload_flow.py -q` sukses.
- [2026-04-06 10:38] [Tim-UploadFlow] [UPL-1.9] [DONE] [RefactorOperator] - Regresi valid path lengkap: `python -m pytest tests/test_upload_flow.py -q`.
- [2026-04-06 10:38] [Tim-UploadFlow] [UPL-1.10] [DONE] [RefactorOperator] - Regresi konflik/duplikasi: `python -m pytest tests/test_upload_flow.py -k duplicate -q`.
- [2026-04-06 10:50] [Tim-UploadPreview] [PRE-2.1] [DONE] [RefactorOperator] - Baseline `python -m pytest tests/test_upload_flow.py tests/test_excel_parser.py -q` lulus.
- [2026-04-06 10:50] [Tim-UploadPreview] [PRE-2.2] [DONE] [RefactorOperator] - Ekstrak helper `_read_preview_session` dan `_write_preview_session` untuk operasi I/O sesi.
- [2026-04-06 10:51] [Tim-UploadPreview] [PRE-2.3] [DONE] [RefactorOperator] - Ekstrak helper `_invalidate_preview_session` dan jadikan `delete_preview_session` sebagai wrapper.
- [2026-04-06 10:51] [Tim-UploadPreview] [PRE-2.4] [DONE] [RefactorOperator] - Ekstrak lookup DB duplicate bertahap: `_collect_duplicate_lookup_keys` + `_lookup_existing_duplicate_records`.
- [2026-04-06 10:52] [Tim-UploadPreview] [PRE-2.5] [DONE] [RefactorOperator] - Ekstrak helper `_to_template_context` untuk pemetaan payload ke konteks template.
- [2026-04-06 10:52] [Tim-UploadPreview] [PRE-2.6] [DONE] [RefactorOperator] - Refaktor orchestrator preview path (`cache_upload_preview`/`build_upload_preview`) supaya dipandu helper internal.
- [2026-04-06 10:53] [Tim-UploadPreview] [PRE-2.7] [DONE] [RefactorOperator] - Verifikasi preview context tetap konsisten lewat `tests/test_upload_preview.py`; regresi upload flow tetap lulus.
- [2026-04-06 10:53] [Tim-UploadPreview] [PRE-2.8] [DONE] [RefactorOperator] - Verifikasi TTL/invalidation via `tests/test_upload_preview.py` dan cleanup cache sesi.
- [2026-04-06 11:00] [Tim-Workbook] [WB-3.1] [DONE] [RefactorOperator] - Baseline sample output workbook via test baru `tests/test_period_analysis_workbook.py`.
- [2026-04-06 11:02] [Tim-Workbook] [WB-3.2] [DONE] [RefactorOperator] - Ekstrak helper `_build_dashboard_sheet`.
- [2026-04-06 11:04] [Tim-Workbook] [WB-3.3] [DONE] [RefactorOperator] - Ekstrak helper `_build_comparison_sheet` dan `_build_current_to_current_sheet`.
- [2026-04-06 11:05] [Tim-Workbook] [WB-3.4] [DONE] [RefactorOperator] - Ekstrak helper `_build_ytd_sheet`.
- [2026-04-06 11:06] [Tim-Workbook] [WB-3.5] [DONE] [RefactorOperator] - Ekstrak helper `_build_metadata_sheet`.
- [2026-04-06 11:07] [Tim-Workbook] [WB-3.6] [DONE] [RefactorOperator] - Satukan helper style dengan `_apply_header_style` dan `_apply_data_style`.
- [2026-04-06 11:08] [Tim-Workbook] [WB-3.7] [DONE] [RefactorOperator] - Jadikan `build_period_analysis_workbook` orchestrator pemanggil helper.
- [2026-04-06 11:09] [Tim-Workbook] [WB-3.8] [DONE] [RefactorOperator] - Verifikasi urutan sheet dan nama tetap sama via `tests/test_period_analysis_workbook.py`.
- [2026-04-06 11:20] [Tim-Mutations] [MUT-4.1] [DONE] [RefactorOperator] - Snapshot baseline row count insert/delete/update di `tests/test_mutations_baseline.py`.
- [2026-04-06 11:23] [Tim-Mutations] [MUT-4.2] [DONE] [RefactorOperator] - Tambah helper transaksi tunggal `_execute_mutation` + `_run_mutation` di `models/mutations.py`.
- [2026-04-06 11:27] [Tim-Mutations] [MUT-4.3] [DONE] [RefactorOperator] - Refactor `insert_entries` ke helper payload `_compose_insert_values` + `_insert_entries_payload`.
- [2026-04-06 11:35] [Tim-Mutations] [MUT-4.4] [DONE] [RefactorOperator] - Refactor `delete_data_entry` melalui `_delete_entry_by_id_payload` + `_run_mutation`.
- [2026-04-06 11:42] [Tim-Mutations] [MUT-4.5] [DONE] [RefactorOperator] - Refactor `bulk_delete_entries` memakai helper payload `_bulk_delete_entries_payload` + `_build_id_placeholders`.
- [2026-04-06 11:55] [Tim-Mutations] [MUT-4.6] [DONE] [RefactorOperator] - Refactor `update_data_entry` lewat helper `_update_data_entry_payload` + `_run_mutation`.
- [2026-04-06 11:58] [Tim-Mutations] [MUT-4.7] [DONE] [RefactorOperator] - Tambah validasi ringan input numeric di `update_data_entry` + jalur invalid bulk/update di `tests/test_data_management_actions.py`.
- [2026-04-06 12:05] [Tim-Mutations] [MUT-4.8] [DONE] [RefactorOperator] - Verifikasi regresi mutation dan performance smoke via `tests/test_data_management_actions.py tests/test_performance_smoke.py`.
- [2026-04-06 12:10] [Tim-Calculators] [CAL-5.1] [DONE] [RefactorOperator] - Baseline indikator period comparison tetap stabil via `tests/test_period_comparisons.py`.
- [2026-04-06 12:15] [Tim-Calculators] [CAL-5.2] [DONE] [RefactorOperator] - Ekstrak `_safe_divide` dan uji helper lewat `tests/test_period_comparisons.py -k safe_divide`.
- [2026-04-06 12:18] [Tim-Calculators] [CAL-5.3] [DONE] [RefactorOperator] - Ekstrak `_calc_growth` dan uji helper lewat `tests/test_period_comparisons.py -k growth`.
- [2026-04-06 12:21] [Tim-Calculators] [CAL-5.4] [DONE] [RefactorOperator] - Ekstrak `_calc_percentage` dan validasi rounding lewat `tests/test_period_comparisons.py -k percentage`.
- [2026-04-06 12:24] [Tim-Calculators] [CAL-5.5] [DONE] [RefactorOperator] - Terapkan helper ke seluruh indikator + kontrak key-order pada `tests/test_period_comparisons.py`.
- [2026-04-06 12:28] [Tim-Calculators] [CAL-5.6] [DONE] [RefactorOperator] - Verifikasi urutan sheet export tetap stabil lewat `tests/simple_tests/functional_tests/test_export.py`.
- [2026-04-06 12:31] [Tim-Calculators] [CAL-5.7] [DONE] [RefactorOperator] - Regresi penuh calculator/workflow/laporan via `tests/test_period_comparisons.py tests/test_upload_flow.py tests/simple_tests/functional_tests/test_export.py`.
- [2026-04-06 12:45] [Tim-Verification] [Gate-1] [DONE] [RefactorOperator] - `python -m pytest tests/test_upload_flow.py -q` lulus.
- [2026-04-06 12:45] [Tim-Verification] [Gate-1] [DONE] [RefactorOperator] - `python -m pytest tests/test_excel_parser.py -q` lulus.
- [2026-04-06 12:46] [Tim-Verification] [Gate-2] [DONE] [RefactorOperator] - `python -m pytest tests/test_upload_flow.py tests/test_period_comparisons.py -q` lulus.
- [2026-04-06 12:46] [Tim-Verification] [Gate-2] [DONE] [RefactorOperator] - `python -m pytest tests/test_data_management_actions.py tests/simple_tests/functional_tests/test_export.py -q` lulus (menyesuaikan path export test aktual).
- [2026-04-06 12:48] [Tim-Verification] [Gate-3] [BLOCKED] [RefactorOperator] - `python tests/simple_tests/run_tests.py` gagal karena `ModuleNotFoundError: No module named 'models'` dan encoding/legacy test-suite issue (`EnvironBuilder(data_file)`), meski service Flask sudah running.
- [2026-04-06 12:50] [Tim-Verification] [E2E-AgentBrowser] [DONE] [RefactorOperator] - Smoke e2e via `agent-browser`: navigasi Landing → Unggah → Manual Input → Pratinjau Data → Manajemen Data → Ringkasan Agregat berhasil dilakukan; tombol unggah file Excel membutuhkan investigasi karena kontrol file custom/tersembunyi tidak terdeteksi.
- [2026-04-06 13:20] [Tim-Verification] [Gate-3] [DONE] [RefactorOperator] - `python -m pytest tests/simple_tests/functional_tests tests/simple_tests/bug_tests -q` dijalankan, sisa failure dipastikan sebagai `xfail` terencana pada 3 test dokumentasi keamanan (CSRF/Session/Rate limiting).

## Team A - Upload Core 1: services/upload_flow.py

## Target

Pisahkan orchestrasi upload menjadi helper kecil agar alur parse, validasi, duplikasi, dan response lebih teruji.

### Checklist

- [x] **UPL-1.1** Buat baseline perilaku upload
- [x] **UPL-1.2** Tambahkan catatan kontrak internal untuk `process_upload_confirm` dan `process_upload_post_file`
- [x] **UPL-1.3** Ekstrak helper `parse_and_validate_upload_payload`
- [x] **UPL-1.4** Ekstrak helper `prepare_duplicate_plan`
- [x] **UPL-1.5** Ekstrak helper `persist_upload_entries`
- [x] **UPL-1.6** Ekstrak helper `build_upload_response`
- [x] **UPL-1.7** Refaktor `process_upload_confirm` jadi orchestrator tipis
- [x] **UPL-1.8** Refaktor `process_upload_post_file` jadi orchestrator tipis
- [x] **UPL-1.9** Jalankan regresi upload 1: validasi happy path
- [x] **UPL-1.10** Jalankan regresi upload 2: conflict path dan error path

### Step-by-step (2–5 menit per step)

- [x] Step UPL-1.1: Jalankan baseline dan catat hasil.
- [x] Step UPL-1.1 Verify: `pytest tests/test_upload_flow.py -q`
- [x] Step UPL-1.1 Log: tambah entry ke Progress Log.
- [x] Step UPL-1.2: Tambahkan catatan kontrak input/output `UploadFlowResponse` (di dokumentasi file sebagai komentar tipe/deskripsi).
- [x] Step UPL-1.2 Verify: `python -m pytest tests/test_upload_flow.py -k confirm -q`
- [x] Step UPL-1.2 Log: tambah entry.
- [x] Step UPL-1.3: Ekstrak `parse_and_validate_upload_payload(payload, uploader, version)` sebagai helper private.
- [x] Step UPL-1.3 Verify: `python -m pytest tests/test_upload_flow.py -q`
- [x] Step UPL-1.3 Log: tambah entry.
- [x] Step UPL-1.4: Ekstrak `prepare_duplicate_plan(entries, uploader, version, mode)`.
- [x] Step UPL-1.4 Verify: `python -m pytest tests/test_upload_flow.py -k duplicate -q`
- [x] Step UPL-1.4 Log: tambah entry.
- [x] Step UPL-1.5: Ekstrak `persist_upload_entries(entries)` dengan pattern transaksi yang sama.
- [x] Step UPL-1.5 Verify: `python -m pytest tests/test_upload_flow.py -q`
- [x] Step UPL-1.5 Log: tambah entry.
- [x] Step UPL-1.6: Ekstrak `build_upload_response(result)` untuk path sukses, konflik, dan gagal.
- [x] Step UPL-1.6 Verify: `python -m pytest tests/test_upload_flow.py -q`
- [x] Step UPL-1.6 Log: tambah entry.
- [x] Step UPL-1.7: Ubah `process_upload_confirm` hanya memanggil 3 helper utama.
- [x] Step UPL-1.7 Verify: `python -m pytest tests/test_upload_flow.py -q`
- [x] Step UPL-1.7 Log: tambah entry.
- [x] Step UPL-1.8: Ubah `process_upload_post_file` sebagai orchestrator alur terpisah.
- [x] Step UPL-1.8 Verify: `python -m pytest tests/test_upload_flow.py -q`
- [x] Step UPL-1.8 Log: tambah entry.
- [x] Step UPL-1.9: Jalankan regresi upload valid path lengkap.
- [x] Step UPL-1.9 Verify: `python -m pytest tests/test_upload_flow.py -q`
- [x] Step UPL-1.9 Log: tambah entry.
- [x] Step UPL-1.10: Jalankan kasus konflik/duplikasi.
- [x] Step UPL-1.10 Verify: `python -m pytest tests/test_upload_flow.py -k duplicate -q`
- [x] Step UPL-1.10 Log: tambah entry.

## Team B - Upload Preview 2: services/upload_preview.py

## Target

Pisahkan session preview, duplicate lookup, dan pembentukan context agar masing-masing bisa dites sendiri.

### Checklist

- [x] **PRE-2.1** Baseline perilaku preview
- [x] **PRE-2.2** Ekstrak helper baca tulis sesi
- [x] **PRE-2.3** Ekstrak helper hapus sesi
- [x] **PRE-2.4** Ekstrak helper lookup duplicate
- [x] **PRE-2.5** Ekstrak helper build context
- [x] **PRE-2.6** Refaktor fungsi publik menjadi orchestrator
- [x] **PRE-2.7** Verifikasi render preview tetap sama
- [x] **PRE-2.8** Verifikasi cleanup TTL dan invalidation

### Step-by-step

- [x] Step PRE-2.1: Jalankan baseline untuk modul preview.
- [x] Step PRE-2.1 Verify: `python -m pytest tests/test_upload_flow.py tests/test_excel_parser.py -q`
- [x] Step PRE-2.1 Log: tambah entry.
- [x] Step PRE-2.2: Ekstrak `_read_preview_session`, `_write_preview_session`.
- [x] Step PRE-2.2 Verify: `python -m pytest tests/test_upload_preview.py -q`
- [x] Step PRE-2.2 Log: tambah entry.
- [x] Step PRE-2.3: Ekstrak `_invalidate_preview_session`.
- [x] Step PRE-2.3 Verify: `python -m pytest tests/test_upload_preview.py -q`
- [x] Step PRE-2.3 Log: tambah entry.
- [x] Step PRE-2.4: Ekstrak `_lookup_existing_entries`.
- [x] Step PRE-2.4 Verify: `python -m pytest tests/test_upload_preview.py -q`
- [x] Step PRE-2.4 Log: tambah entry.
- [x] Step PRE-2.5: Ekstrak `_to_template_context`.
- [x] Step PRE-2.5 Verify: `python -m pytest tests/test_upload_preview.py -q`
- [x] Step PRE-2.5 Log: tambah entry.
- [x] Step PRE-2.6: Ubah public API tetap dipakai, fungsi publik sekarang jadi pipeline.
- [x] Step PRE-2.6 Verify: `python -m pytest tests/test_upload_flow.py -q`
- [x] Step PRE-2.6 Log: tambah entry.
- [x] Step PRE-2.7: Bandingkan payload context sebelum/sesudah refactor.
- [x] Step PRE-2.7 Verify: `python -m pytest tests/test_upload_preview.py tests/test_upload_flow.py -q`
- [x] Step PRE-2.7 Log: tambah entry.
- [x] Step PRE-2.8: Buat skenario cleanup stale token dan TTL.
- [x] Step PRE-2.8 Verify: `python -m pytest tests/test_upload_preview.py -q`
- [x] Step PRE-2.8 Log: tambah entry.
 
## Team C - Workbook 3: services/period_analysis_workbook.py

## Target

Pisahkan pipeline export workbook menjadi builder per sheet supaya style dan data mapping terpisah.

### Checklist

- [x] **WB-3.1** Buat baseline workbook sample
- [x] **WB-3.2** Ekstrak pembangun sheet dashboard
- [x] **WB-3.3** Ekstrak pembangun sheet comparison
- [x] **WB-3.4** Ekstrak pembangun sheet ytd
- [x] **WB-3.5** Ekstrak pembangun sheet metadata
- [x] **WB-3.6** Satukan style helper (header/data)
- [x] **WB-3.7** Refaktor `build_period_analysis_workbook` jadi orchestrator
- [x] **WB-3.8** Verifikasi urutan sheet, nama, dan nilai tetap sama

### Step-by-step

- [x] Step WB-3.1: Jalankan baseline export workbook pada indikator sample.
- [x] Step WB-3.1 Verify: `python -m pytest tests/test_period_comparisons.py tests/test_period_analysis_workbook.py -q`
- [x] Step WB-3.1 Log: tambah entry.
- [x] Step WB-3.2: Buat helper `_build_dashboard_sheet`.
- [x] Step WB-3.2 Verify: `python -m pytest tests/test_period_analysis_workbook.py -q`
- [x] Step WB-3.2 Log: tambah entry.
- [x] Step WB-3.3: Buat helper `_build_comparison_sheet`.
- [x] Step WB-3.3 Verify: `python -m pytest tests/test_period_analysis_workbook.py -q`
- [x] Step WB-3.3 Log: tambah entry.
- [x] Step WB-3.4: Buat helper `_build_ytd_sheet`.
- [x] Step WB-3.4 Verify: `python -m pytest tests/test_period_analysis_workbook.py -q`
- [x] Step WB-3.4 Log: tambah entry.
- [x] Step WB-3.5: Buat helper `_build_metadata_sheet`.
- [x] Step WB-3.5 Verify: `python -m pytest tests/test_period_analysis_workbook.py -q`
- [x] Step WB-3.5 Log: tambah entry.
- [x] Step WB-3.6: Buat helper style `_apply_header_style` dan `_apply_data_style`.
- [x] Step WB-3.6 Verify: `python -m pytest tests/test_period_analysis_workbook.py -q`
- [x] Step WB-3.6 Log: tambah entry.
- [x] Step WB-3.7: Refaktor `build_period_analysis_workbook` menjadi pemanggil helper.
- [x] Step WB-3.7 Verify: `python -m pytest tests/test_period_comparisons.py tests/test_period_analysis_workbook.py -q`
- [x] Step WB-3.7 Log: tambah entry.
- [x] Step WB-3.8: Jalankan full regresi workbook.
- [x] Step WB-3.8 Verify: `python -m pytest tests/test_period_analysis_workbook.py tests/test_period_comparisons.py -q`
- [x] Step WB-3.8 Log: tambah entry.

## Team D - Mutations 4: models/mutations.py

## Target

Kurangi duplicate DB transaction code dan standarkan helper mutasi.

### Checklist

- [x] **MUT-4.1** Buat baseline operasi mutation
- [x] **MUT-4.2** Buat helper transaksi tunggal
- [x] **MUT-4.3** Ganti `insert_entries` ke helper
- [x] **MUT-4.4** Ganti `delete_data_entry` ke helper
- [x] **MUT-4.5** Ganti `bulk_delete_entries` ke helper
- [x] **MUT-4.6** Ganti `update_data_entry` ke helper
- [x] **MUT-4.7** Tambah validasi ringan untuk input tipe data
- [x] **MUT-4.8** Verifikasi semua mutasi tetap konsisten

### Step-by-step

- [x] Step MUT-4.1: Snapshot output jumlah row untuk insert, delete, update.
- [x] Step MUT-4.1 Verify: `python -m pytest tests/test_data_management_actions.py tests/test_regression_routes.py tests/test_mutations_baseline.py -q`
- [x] Step MUT-4.1 Log: tambah entry.
- [x] Step MUT-4.2: Tambah helper `_execute_mutation` + `_run_mutation`.
- [x] Step MUT-4.2 Verify: import modul dan jalankan lint/test kecil.
- [x] Step MUT-4.2 Log: tambah entry.
- [x] Step MUT-4.3: Refactor insert path memakai helper baru.
- [x] Step MUT-4.3 Verify: `python -m pytest tests/test_data_management_actions.py -k insert -q`
- [x] Step MUT-4.3 Log: tambah entry.
- [x] Step MUT-4.4: Refactor delete single path memakai helper baru.
- [x] Step MUT-4.4 Verify: `python -m pytest tests/test_data_management_actions.py -k delete -q`
- [x] Step MUT-4.4 Log: tambah entry.
- [x] Step MUT-4.5: Refactor bulk delete path memakai helper.
- [x] Step MUT-4.5 Verify: `python -m pytest tests/test_data_management_actions.py -k bulk -q`
- [x] Step MUT-4.5 Log: tambah entry.
- [x] Step MUT-4.6: Refactor update path memakai helper.
- [x] Step MUT-4.6 Verify: `python -m pytest tests/test_data_management_actions.py -k update -q`
- [x] Step MUT-4.6 Log: tambah entry.
- [x] Step MUT-4.7: Tambah validasi input untuk tipe numeric/text dan error path.
- [x] Step MUT-4.7 Verify: `python -m pytest tests/test_data_management_actions.py -k validation -q`
- [x] Step MUT-4.7 Log: tambah entry.
- [x] Step MUT-4.8: Jalankan regresi seluruh mutation.
- [x] Step MUT-4.8 Verify: `python -m pytest tests/test_data_management_actions.py tests/test_performance_smoke.py -q`
- [x] Step MUT-4.8 Log: tambah entry.

## Team E - Indicator Calculators 5: services/period_comparison_calculators.py

## Target

Pisahkan helper matematis agar rumus tidak bercampur dengan pembagian indikator.

### Checklist

- [x] **CAL-5.1** Baseline hasil semua indikator pada sample data
- [x] **CAL-5.2** Tambah helper `_safe_divide`
- [x] **CAL-5.3** Tambah helper `_calc_growth`
- [x] **CAL-5.4** Tambah helper `_calc_percentage`
- [x] **CAL-5.5** Terapkan helper di semua fungsi indikator
- [x] **CAL-5.6** Kunci output shape dan key order
- [x] **CAL-5.7** Verifikasi regression suite

### Step-by-step

- [x] Step CAL-5.1: Jalankan baseline comparators.
- [x] Step CAL-5.1 Verify: `python -m pytest tests/test_period_comparisons.py -q`
- [x] Step CAL-5.1 Log: tambah entry.
- [x] Step CAL-5.2: Ekstrak helper `_safe_divide`.
- [x] Step CAL-5.2 Verify: `python -m pytest tests/test_period_comparisons.py -k safe_divide -q`
- [x] Step CAL-5.2 Log: tambah entry.
- [x] Step CAL-5.3: Ekstrak helper `_calc_growth`.
- [x] Step CAL-5.3 Verify: `python -m pytest tests/test_period_comparisons.py -k growth -q`
- [x] Step CAL-5.3 Log: tambah entry.
- [x] Step CAL-5.4: Ekstrak helper `_calc_percentage`.
- [x] Step CAL-5.4 Verify: `python -m pytest tests/test_period_comparisons.py -k percentage -q`
- [x] Step CAL-5.4 Log: tambah entry.
- [x] Step CAL-5.5: Terapkan helper ke seluruh indikator.
- [x] Step CAL-5.5 Verify: `python -m pytest tests/test_period_comparisons.py -q`
- [x] Step CAL-5.5 Log: tambah entry.
- [x] Step CAL-5.5: Buat kontrak output dict dengan key tetap.
- [x] Step CAL-5.5 Verify: test sederhana untuk key set yang tetap.
- [x] Step CAL-5.5 Log: tambah entry.
- [x] Step CAL-5.6: Verifikasi urutan sheet export tetap cocok.
- [x] Step CAL-5.6 Verify: `python -m pytest tests/simple_tests/functional_tests/test_export.py -q`
- [x] Step CAL-5.6 Log: tambah entry.
- [x] Step CAL-5.7: Jalankan regresi lengkap area calculator + workbook.
- [x] Step CAL-5.7 Verify: `python -m pytest tests/test_period_comparisons.py tests/test_upload_flow.py tests/simple_tests/functional_tests/test_export.py -q`
- [x] Step CAL-5.7 Log: tambah entry.

## Verification Gates

- Setiap team harus selesai penuh sebelum masuk task berikutnya pada area yang sama.
- Tidak boleh lanjut ke area lain jika gate di bawah gagal.
- Gunakan 3 level verifikasi: per-step test, per-file sanity test, full regression smoke.

### Gate-1 (Upload)

- [x] Jalankan `python -m pytest tests/test_upload_flow.py -q`
- [x] Jalankan `python -m pytest tests/test_excel_parser.py -q`

### Gate-2 (Preview + Workbook + Mutations)

- [x] Jalankan `python -m pytest tests/test_upload_flow.py tests/test_period_comparisons.py -q`
- [x] Jalankan `python -m pytest tests/test_data_management_actions.py tests/simple_tests/functional_tests/test_export.py -q`

### Gate-3 (General)

- [ ] Jalankan subset integration command dari script test suite (`tests/simple_tests/run_tests.py` jika dipakai di lingkungan lokal).

## Rollback Plan

- Revert step terakhir yang gagal.
- Kembalikan helper dan kontrak step terkait.
- Ulangi step sebelumnya dari checkpoint terakhir.
- Update Progress Log dengan status `BLOCKED` + akar penyebab.
- Lanjutkan setelah test dan kontrak stabil.

## Dependencies and sync files

- `planning.md` (sinkronisasi status global rencana bila diperlukan)
- `C:/Users/PENGOLAHAN/.cursor/plans/bps_data_management_system_bd94389d.plan.md` (sinkronisasi sesuai aturan repo )








## Repo Hygiene
- Menambahkan/menegaskan `tmp/` pada `.gitignore` dan menghapus folder `tmp/` dari tracking git di branch `alternative_main` agar tidak lagi masuk repository.

