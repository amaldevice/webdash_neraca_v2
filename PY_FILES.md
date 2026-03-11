# Ringkasan File Python (`.py`)

Dokumen ini mengumpulkan penjelasan seluruh berkas Python utama agar agent bisa memahami alur fitur tanpa membaca semua file detail terlebih dahulu.

## `app.py`

- Menjadi entrypoint Flask dan orchestrator request.
- Menyimpan konfigurasi app (`UPLOAD_FOLDER`, `DATABASE`, `MAX_CONTENT_LENGTH`, `SECRET_KEY`).
- Menyediakan helper validasi:
  - `allowed_file()`: validasi ekstensi upload Excel.
  - `validate_metadata()`: cek `data_type` dan `time_period`.
  - `_parse_period_date()`: normalisasi format periode dari input manual.
  - `_build_manual_entry()`: bangun dict entri manual lengkap.
  - `_get_range_params()`, `get_available_years()`: parse query/pagination.
- Endpoint utama:
  - `/` landing
  - `/upload`, `/manual`
  - `/preview-data`
  - `/data-management`
  - `/export`
- Endpoint analitik:
  - `/generate-plot`
  - `/generate-period-analysis`
  - `/export-period-analysis`
- Menangani alur:
  - upload file Excel → parse di `excel_parser.py` → simpan via `models.py`
  - input manual (single entry) → validasi + insert
  - export data dan filter dinamis
  - panggil `aggregator.refresh_aggregated_summary()` saat ada insert/update agar cache ringkasan terbarui

## `aggregator.py`

- Layer cache/aggregate ringan untuk performa tampilan:
  - `refresh_aggregated_summary()`
    - ambil metadata + summary cards dari `models`.
    - update `aggregated_summary` table.
  - `fetch_aggregated_summary()`
    - ambil cache siap pakai untuk landing / dashboard.
    - fallback refresh jika cache belum ada.
- Inti: memisahkan pengambilan ringkasan berat dari request preview biasa.

## `excel_parser.py`

- Fokus pada parsing file Excel menjadi struktur data standar sebelum insert DB.
- `detect_template_format()`
  - mendeteksi apakah layout file memakai pola horizontal atau vertikal.
- Helper transform:
  - `_to_float()` untuk normalisasi angka.
  - `_parse_period()` parser periode (`YYYY`, `YYYY-MM`, `YYYY-QN`).
  - `_normalize_record()` menyamakan key-value agar seragam ke skema DB.
- `parse_vertical_layout()` dan `parse_horizontal_layout()`
  - membaca sheet sesuai struktur masing-masing format.
- `parse_excel(file_storage, metadata)` (fungsi utama)
  - orchestrasi baca file, deteksi format, parse, dan hasilkan list dict siap persist.

## `models.py`

- Akses data SQLite dan semua operasi persistensi.
- Inisialisasi DB:
  - `init_db()`, `get_conn()`
  - schema `data_entries` dan `aggregated_summary` + index unik
- CRUD dasar dan query:
  - `insert_entries()`, `query_data_entries()`, `get_total_entries_count()`
  - `update_data_entry()`, `update_data_entry_full()`, `delete_data_entry()`
  - `delete_data_by_filter()`, `bulk_delete_entries()`, `bulk_update_entries()`
  - `insert_single_entry()` untuk input manual
- Filtering periode:
  - `_parse_period_filter_value()`, `_apply_period_range_filter()`
  - mendukung format `YYYY`, `YYYY-MM`, `YYYY-Qn`
- Utilitas metadata:
  - `get_filter_options()`, `get_unique_indicators()`
- Agregasi dan cache:
  - `save_aggregated_summary()`, `load_cached_summary()`, `get_aggregated_cards()`, `get_latest_metadata()`
- Analisis periodik:
  - `calculate_period_comparisons()`
  - helper: `calculate_monthly_comparison()`, `calculate_quarterly_comparison()`, `calculate_yearly_comparison()`, `calculate_ytd_comparison()`, `calculate_current_to_current()`
- Penunjang fitur:
  - `get_total_entries_count()`, pemecahan string indicator metadata, dan query helper agar endpoint analitik tetap konsisten.
