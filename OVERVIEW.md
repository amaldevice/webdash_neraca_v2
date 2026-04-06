# Ringkasan Cepat Struktur Proyek

Dokumen ini memberikan gambaran tidak general per folder dan per file utama agar agent bisa paham konteks inti tanpa membuka satu per satu dulu.

## Root (`d:\webdash_neraca\`)

- Menyimpan semua file aplikasi inti dan konfigurasi runtime.
- Berkas utama backend: `app.py` (factory), paket **`excel_parser/`**, paket **`models/`**, shim `aggregator.py`.
- Rute HTTP: paket **`routes/`**; logika layanan: **`services/`** (termasuk `upload_flow`, `upload_preview`).
- UI template di `templates/`, style di `assets/` dan `static/`.
- **E2E:** `e2e/` + `playwright.config.ts` + root `package.json` (`npm run test:e2e`). CSS Tailwind dapat memakai `metadata/package.json` terpisah.

## `assets/`

- `assets/tailwind.css`  
  Source-of-truth untuk tema awal Tailwind/DaisyUI:
  - mendeklarasikan `@tailwind base/components/utilities`.
  - diproses pada saat build menjadi CSS siap pakai di `static/css/tailwind.css`.

## `static/`

- `static/css/tailwind.css`  
  Output final build dari `assets/tailwind.css` (hasil kompilasi Tailwind + utility baseline).
- `static/css/style.css`  
  CSS kustom untuk tampilan dan interaksi:
  - style topbar, tabel data, mode aksesibilitas focus, status/alert, tab period analysis, dan media-query.
  - dipakai untuk penyempurnaan UI yang tidak ideal diletakkan di utility layer.

## `templates/` (halaman + partials)

- `base_tailwind.html`  
  Layout utama app: topbar, menu nav, branding, tema, flash messages, wrapper konten, footer.
- `landing.html`  
  Halaman Beranda Dashboard: kartu statistik dan aksi cepat (unggah/manual/aggregat).
- `upload.html`  
  Halaman wrapper untuk unggah Excel dan input manual; menampilkan form yang sesuai mode (`upload`/`manual`).
- `preview.html`  
  Halaman pratinjau data dengan filter + tabel list + ekspor CSV/Excel.
- `data_management.html`  
  Halaman manajemen data: filter + tambah data + tabel CRUD + modal edit + aksi massal.
- `aggregated.html`  
  Halaman analisis agregat: form periode, plot line, dan analisis perbandingan periode.

### `templates/partials/`

- `_nav_menu_items.html`  
  Definisi menu utama dan state aktif berdasarkan endpoint saat ini.
- `_page_header.html`  
  Header reusable dengan judul, deskripsi, dan tombol aksi konteks halaman.
- `_flash_messages.html`  
  Renderer notifikasi flash server (success/error/warning/info) dengan tombol tutup.
- `_landing_summary_cards.html`  
  Kartu ringkasan KPI untuk halaman landing.
- `_upload_form.html`  
  Form unggah Excel lengkap field uploader/version/data_type/time_period/file.
- `_manual_form.html`  
  Form input manual, termasuk helper period format dinamis.
- `_preview_filters.html`  
  Filter halaman preview (data type, period, uploader, indikator, rentang periode, limit, quick reset).
- `_preview_table.html`  
  Tabel pratinjau data + pagination include.
- `_management_filters.html`  
  Filter halaman manajemen data (sama pola dengan preview, plus aksi hapus by filter).
- `_management_insert_form.html`  
  Form tambah data tunggal di halaman manajemen.
- `_management_table.html`  
  Tabel manajemen data (mobile + desktop), checkbox selection, edit/hapus row.
- `_management_bulk_modal.html`  
  Modal untuk bulk update dan konfirmasi aksi.
- `_script_preview_filters.html`  
  JS untuk status/filter cepat, shortcut Ctrl+Enter, dan perubahan limit.
- `_script_management_bulk_actions.html`  
  JS inti aksi massal (bulk delete/update), selection state, dialog konfirmasi, edit modal, format helper.
- `_aggregated_plot_form.html`  
  Form request grafik line (indikator, rentang waktu, range opsional).
- `_aggregated_period_form.html`  
  Form request analisis periodik (indikator, tahun, period_start/end).
- `_script_aggregated_analysis.html`  
  JS untuk generate plot, generate analisis periodik, render HTML tabel, tab switching, export excel analisis.
- `_data_type_badge.html`  
  Komponen badge tipe data (flow/stock).
- `_time_period_badge.html`  
  Komponen badge periode (bulanan/triwulanan/tahunan).
- `_empty_state.html`  
  Placeholder/tampilan saat tidak ada data pada konteks tertentu.
- `_pagination.html`  
  Komponen pagination reusable (Previous/Next + page range).
- `_script_theme_toggle.html`  
  Toggle tema light/dark localStorage dan `data-theme`.
- `_script_upload_period_format.html`  
  JS helper ubah contoh format input periode saat jenis periode upload/manual berubah.

## `app.py`

Ini layer orchestration web:

- Inisialisasi app, konfigurasi upload/db path/secret key.
- Helper validasi:
  - `allowed_file()`: cek ekstensi Excel.
  - `validate_metadata()`: validasi `data_type` dan `time_period`.
  - `_parse_period_date()` dan `_build_manual_entry()` untuk normalisasi input manual.
  - `_get_range_params()` dan `get_available_years()` untuk parameter filter.
- Route utama:
  - `/` landing, `/upload`, `/manual`, `/preview-data`, `/export`, `/aggregated`, `/data-management`.
- Route analitik:
  - `/generate-plot`, `/generate-period-analysis`, `/export-period-analysis`.
- Export:
  - CSV dan Excel raw data (export endpoint mempertahankan filter aktif).
- Grafik:
  - `generate_indicator_line_chart()` menghasilkan `plot_json` Plotly untuk klien render.
- Menjalankan `refresh_aggregated_summary()` setelah insert/update/bulk insert.

## `aggregator.py`

- `refresh_aggregated_summary()`  
  Mengambil metadata terbaru + kartu agregat dari `models`, menyimpan ke cache.
- `fetch_aggregated_summary()`  
  Mengambil cache apabila ada, fallback ke refresh bila kosong.

## `excel_parser.py`

- `detect_template_format()`  
  Menebak mode template: `horizontal` atau `vertical`.
- `_to_float()`, `_parse_period()`, `_normalize_record()`  
  Helper parsing dan normalisasi ke skema record seragam.
- `_parse_horizontal_layout()` dan `_parse_vertical_layout()`  
  Penanganan dua bentuk template Excel.
- `parse_excel()`  
  Orkestrator parse file ke list dict siap simpan.

## `models.py`

- Koneksi dan skema:
  - `init_db()`, `get_conn()`, tabel `data_entries` dan `aggregated_summary`.
  - indeks unique (`uploader_name`, `version`, `indicator_name`, `year`, `month`, `quarter`).
- Insert/read/write:
  - `insert_entries()`, `get_total_entries_count()`, `query_data_entries()`.
  - `update_data_entry()`, `update_data_entry_full()`, `delete_data_entry()`, `delete_data_by_filter()`.
- Filter periode:
  - `_parse_period_filter_value()`, `_apply_period_range_filter()`, dukungan parsing `YYYY`, `YYYY-MM`, `YYYY-Qn`.
- Agregasi cache:
  - `save_aggregated_summary()`, `load_cached_summary()`, `get_aggregated_cards()`, `get_latest_metadata()`.
- Metadata helper:
  - `get_filter_options()`, `get_unique_indicators()`.
- CRUD tambahan & operasional:
  - `insert_single_entry()`, `bulk_delete_entries()`, `bulk_update_entries()`.
- Perhitungan analisis:
  - `calculate_period_comparisons()` + helper `calculate_monthly_comparison()`,
    `calculate_quarterly_comparison()`, `calculate_yearly_comparison()`,
    `calculate_ytd_comparison()`, `calculate_current_to_current()`.
