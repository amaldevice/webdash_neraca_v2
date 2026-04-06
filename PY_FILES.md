# Ringkasan File Python (`.py`)

Dokumen ini mengumpulkan penjelasan seluruh berkas Python utama agar agent bisa memahami alur fitur tanpa membaca semua file detail terlebih dahulu.

## `app.py`

- **Factory** Flask: `create_app(testing=...)` memanggil `configure_flask_app` dari `config.py`, `register_routes(app)` dari paket `routes/`, dan `init_db()`.
- Ekspor modul `app = create_app()` untuk WSGI / impor lama.
- Alias kompatibilitas tes: `_parse_period_date`, `_build_manual_entry`, re-export `allowed_file`, `validate_metadata` dari `services.validation`.
- Rute konkret didaftarkan di `routes/pages.py`, `routes/upload_routes.py`, `routes/manage.py` (bukan lagi seluruhnya di `app.py`).

## `aggregator.py`

- Layer cache/aggregate ringan untuk performa tampilan:
  - `refresh_aggregated_summary()`
    - ambil metadata + summary cards dari `models`.
    - update `aggregated_summary` table.
  - `fetch_aggregated_summary()`
    - ambil cache siap pakai untuk landing / dashboard.
    - fallback refresh jika cache belum ada.
- Inti: memisahkan pengambilan ringkasan berat dari request preview biasa.

## Paket `excel_parser/`

- **`constants.py`** — `MAX_DETECTION_ROWS`, `MAX_LAYOUT_LOOKAHEAD_ROWS`, `PREVIEW_SAMPLE_LIMIT`.
- **`normalize.py`** — `_to_float`, `_parse_period`, `_trim_sparse_data`, helper sel kosong / mirip-periode.
- **`layout.py`** — `detect_template_format`, `_detect_layout`, `_materialize_data_frame`.
- **`records.py`** — `_normalize_record`, `_period_text` (skema DB + timestamp ISO).
- **`parse_layouts.py`** — `_parse_vertical_layout`, `_parse_horizontal_layout`.
- **`payload.py`** — **`parse_excel_payload`**, `parse_excel` (orkestrasi `read_excel` + fallback legacy).
- **`__init__.py`** — re-export API publik + simbol internal untuk tes (`from excel_parser import …`).

## Paket `models/`

- **`connection`**: `DB_PATH`, `init_db()`, `get_conn()` (path efektif dari `models.DB_PATH` agar tes bisa monkeypatch).
- **`mutations`**: insert/update/delete/bulk, `clear_all_data`, dll.
- **`queries`**: `query_data_entries`, `get_total_entries_count`, …
- **`browse`**: kartu agregat, filter options, metadata, tahun distinct, indikator unik.
- **`summary_store`**: `save_aggregated_summary`, `load_cached_summary`.
- **`data_filters`**: klausa filter SQL bersama untuk query/hapus.
- **`__init__.py`**: re-export API publik + fungsi analitik periode dari `services.period_comparisons`.
