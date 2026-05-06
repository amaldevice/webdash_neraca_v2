# PRD: Dead Code Removal — Chart/Analysis Layer, Fragmented Float Utilities & Stale Docs

## Problem Statement

Developer yang membaca codebase menemukan file, fungsi, dan import yang mengacu pada fitur yang sudah dihapus (chart visualisasi, period comparison analysis) maupun duplikasi utility (`_to_float` tiga implementasi terpisah). Situasi ini menyebabkan:

1. **Kebingungan scope** — `services/charts.py`, `fetch_series_for_comparison`, dan referensi `period_comparisons.py` / `period_comparison_calculators.py` di dokumentasi membuat developer berasumsi fitur dashboard/analisis masih aktif, padahal sudah dihapus.
2. **Maintenance overhead** — Tiga implementasi `_to_float` yang berbeda (di `models/mutations.py`, `excel_parser/normalize.py`, dan `services/request_params.py`) dengan behaviour berbeda (yang di `excel_parser` handles locale comma/dot, yang lain tidak).
3. **Test coupling salah** — Test mengimport `_parse_period_date` dan `_build_manual_entry` dari `app.py` (via legacy aliases) alih-alih dari source aslinya (`periods.py` dan `services/manual_entries.py`). Ini membuat `app.py` jadi test surface palsu.
4. **Dependency phantom** — `plotly==6.5.0` masih ada di `requirements.txt` meski satu-satunya konsumennya (`services/charts.py`) sudah tidak dipanggil dari manapun.
5. **Import noise** — `services/upload_flow.py` mengimport 4 simbol dari `upload_form` yang tidak digunakan di body-nya (routes mengimport langsung). `models/repositories/__init__.py` re-export dua simbol yang tidak pernah dipakai via path itu.

## Solution

Hapus semua dead code terkait chart/analisis, konsolidasikan `_to_float` ke satu implementasi, bersihkan alias test, hapus import phantom, dan update dokumentasi agar mencerminkan scope aktual aplikasi: **upload, simpan, filter, dan ekspor data mentah saja**.

## User Stories

1. Sebagai developer baru, saya ingin `services/` hanya berisi module yang aktif dipakai, sehingga saya tidak membuang waktu menelusuri `charts.py` yang ternyata tidak terhubung ke manapun.
2. Sebagai developer, saya ingin `requirements.txt` hanya mencantumkan dependency yang benar-benar digunakan runtime, sehingga `pip install` tidak menarik `plotly` yang tidak perlu.
3. Sebagai developer, saya ingin satu fungsi `_to_float` yang handles locale (comma/dot), sehingga tidak ada risiko parsing angka yang berbeda-beda tergantung dari layer mana data mengalir.
4. Sebagai developer, saya ingin test mengimport langsung dari source module (`periods.py`, `services/manual_entries.py`), sehingga perubahan di `app.py` tidak memengaruhi test utility.
5. Sebagai developer, saya ingin `models/queries.py` tidak mengandung fungsi yang hanya dipanggil dari test dan tidak punya consumer di service/route aktif, sehingga surface API model tetap minimal.
6. Sebagai developer, saya ingin `docs/CONTEXT.md` dan `docs/codebase/ARCHITECTURE.md` mencerminkan arsitektur aktual (tanpa fitur period comparison), sehingga tidak ada mismatch antara docs dan kode.
7. Sebagai developer, saya ingin `services/upload_flow.py` tidak mengandung import yang tidak dipakai, sehingga lint dan code review tidak terganggu noise.
8. Sebagai developer, saya ingin `models/__init__.py` tidak meng-ekspos simbol private (`_to_float`) di `__all__`, sehingga public API module tidak leaky.
9. Sebagai developer, saya ingin plan doc yang sudah dieksekusi (`docs/plans/2026-05-04-remove-legacy-sql.md`) diarsip, sehingga `docs/plans/` hanya berisi pekerjaan aktual yang belum selesai.
10. Sebagai developer, saya ingin `app.py` tidak mengekspos alias `_parse_period_date` dan `_build_manual_entry` yang hanya ada untuk test, sehingga `app.py` tetap bersih sebagai factory saja.
11. Sebagai developer, saya ingin `models/mutations.py` hanya punya satu internal float coercion helper (bukan dua yang identik), sehingga tidak ada pertanyaan "pakai yang mana".
12. Sebagai developer, saya ingin `models/repositories/__init__.py` tidak mengekspos re-export yang tidak pernah dipakai, sehingga tidak ada jalan import palsu yang muncul di autocomplete.

## Implementation Decisions

### Modul yang dihapus
- `services/charts.py` — seluruh file. Tidak ada caller di routes/templates/services aktif. Satu-satunya referensi ada di docs.
- `models/queries.py::fetch_series_for_comparison()` — orphan function; consumer-nya (`services/period_comparisons.py`) sudah dihapus. Test yang memanggilnya ikut dihapus.

### Konsolidasi `_to_float`
- Satu implementasi authoritative: yang ada di `excel_parser/normalize.py` — paling lengkap (handles string locale, non-ASCII space, comma/dot ambiguity).
- `models/mutations.py` — hapus exported `_to_float`; rename `_to_valid_float` → `_to_float` sebagai private internal helper (simple `float()` coercion cukup di layer ini karena nilai sudah angka saat sampai model).
- `services/request_params.py` — ganti definisi lokal `_to_float` dengan import dari `excel_parser.normalize._to_float` agar parsing nilai filter konsisten dengan parser Excel.
- `models/__init__.py` — hapus `_to_float` dari import dan `__all__`.

### Pembersihan alias `app.py`
- Hapus `_parse_period_date = parse_period_date` dan `_build_manual_entry = build_manual_entry` dari `app.py`.
- Hapus kedua simbol dari `__all__` di `app.py`.
- Update `tests/test_bugs.py` dan `tests/test_app_utils.py`: import `_parse_period_date` langsung dari `periods` dan `_build_manual_entry` dari `services.manual_entries`.

### Pembersihan import noise
- `services/upload_flow.py` — hapus 4 import dari `upload_form` (`collect_upload_file_errors`, `normalize_upload_action`, `parse_upload_form`, `save_uploaded_excel`) yang tidak dipakai di body file tersebut.
- `models/repositories/__init__.py` — hapus re-export `fetch_entries_for_list` dan `count_entries_for_list` (caller pakai direct import dari `models.repositories.entry_list`).

### Dependency
- `requirements.txt` — hapus `plotly==6.5.0`. `pandas` tetap dipertahankan (dipakai di `excel_parser/`, `services/raw_export.py`, dan tests).

### Dokumentasi yang harus diupdate
- `docs/CONTEXT.md` — hapus baris "Dashboard memakai `services/period_comparison_calculators.py` dan `services/period_comparisons.py`"; update arsitektur ringkas ke scope aktual.
- `docs/codebase/ARCHITECTURE.md` — hapus section "Alur Analisis & Ekspor", hapus referensi `services/charts.py`, `services/period_*`, `period_analysis_workbook`; update "Tujuan" untuk tidak menyebut analisis perbandingan periode.
- `docs/codebase/STACK.md` — hapus "Visualisasi: plotly 6.5.0".
- `docs/codebase/STRUCTURE.md` — hapus referensi `services/period_analysis_workbook.py`, `services/period_comparisons`, dashboard analisis; update deskripsi routes `manage.py` ke fungsi aktualnya (CRUD data management).
- `docs/plans/2026-05-04-remove-legacy-sql.md` — pindahkan ke `docs/plans/archive/` (plan sudah dieksekusi sepenuhnya).
- `docs/README_DOCS.md` — tambah entry changelog bertanggal.
- `.cursor/plans/bps_data_management_system_bd94389d.plan.md` — tambah todo `dead-code-removal-chart-analysis` dengan status `completed` setelah dikerjakan.

### Dependency direction (tetap bersih setelah perubahan)
```
routes/  →  services/  →  models/  →  infrastructure/
                ↓
           excel_parser/   (services.request_params → excel_parser.normalize._to_float)
```
`models/` tidak mengimport dari `excel_parser/` — coercion sederhana di mutations tetap lokal.

## Testing Decisions

- **Prinsip:** Hanya test perilaku eksternal. Test untuk utility internal (`_to_float`, `_to_valid_float`) yang sudah dikonsolidasi tidak perlu dipertahankan sebagai unit test tersendiri — cukup covered oleh integration path (upload, parse, insert).
- **Modul yang diuji setelah perubahan:**
  - `tests/test_bugs.py` — update import, pastikan test yang menguji `_to_float` sudah mengarah ke `excel_parser.normalize._to_float`. Test behaviournya identik, tidak perlu rewrite.
  - `tests/test_app_utils.py` — update import `_build_manual_entry` ke source asli.
  - `tests/test_queries_sqlalchemy.py` — hapus `test_fetch_series_for_comparison_on_sa` karena fungsinya dihapus.
  - Seluruh test suite harus pass tanpa modifikasi logic setelah setiap langkah. `pytest` adalah gate utama.
- **Prior art:** Pattern import update ini sama dengan refactor yang dilakukan saat decomposition `upload_flow.py` (lihat riwayat `tests/test_upload_flow.py`).

## Out of Scope

- Refactor lebih lanjut pada `models/repositories/entry_list.py` (thin pass-through layer — dipertahankan sebagai abstraction point untuk ekspansi future).
- Penghapusan `services/raw_export.py` — ini masih aktif (dipakai di `routes/pages.py` untuk `/export`).
- Penghapusan `numpy` dari `requirements.txt` — perlu verifikasi apakah pandas / openpyxl masih menariknya sebagai transitive dependency.
- Penambahan fitur baru apapun.
- Linting/formatter configuration.
- CI/CD pipeline setup.

## Further Notes

- Scope yang tersisa dari aplikasi setelah cleanup: **Upload (Excel + manual) → Simpan → Filter → Ekspor data mentah**. Tidak ada fitur chart, pivot, atau analisis periodik.
- `services/charts.py` mengimport `pandas` — setelah dihapus, `pandas` masih dipakai di `excel_parser/` dan `services/raw_export.py`, sehingga baris `pandas` di `requirements.txt` tetap ada.
- Eksekusi disarankan berurutan per grup: (1) hapus file/fungsi dead, (2) konsolidasi `_to_float`, (3) bersihkan import/alias, (4) update docs — dengan `pytest` green di setiap langkah.
- Referensi sejarah fitur analisis yang dihapus tetap tersedia di `docs/superpowers/plans/` untuk audit trail, tidak perlu dihapus.
