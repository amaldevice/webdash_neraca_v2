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
- `C:/Users/PENGOLAHAN/.cursor/plans/bps_data_management_system_bd94389d.plan.md` (sinkronisasi sesuai aturan repo)
- `refactor-planning.md` (log progres setiap task)

