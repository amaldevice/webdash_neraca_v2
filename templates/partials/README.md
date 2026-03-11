# templates/partials/

Kumpulan komponen dan fragment Jinja2 yang direuse di beberapa halaman.

## Daftar Partial (utama)

- `_nav_menu_items.html`  
  Menyusun daftar menu utama dan memberi state aktif berdasarkan endpoint saat ini.
- `_page_header.html`  
  Komponen header halaman (judul, deskripsi, tombol aksi).
- `_flash_messages.html`  
  Tampil notifikasi flash (`success`, `error`, `warning`, `info`) dengan tombol tutup.
- `_landing_summary_cards.html`  
  Kartu ringkasan nilai/indicator untuk halaman landing.
- `_upload_form.html`  
  Form unggah Excel (field metadata + file).
- `_manual_form.html`  
  Form input manual + helper format periode dinamis.
- `_preview_filters.html`  
  Filter halaman pratinjau (type, period, range, uploader, indikator, limit).
- `_preview_table.html`  
  Tabel pratinjau data + pagination include.
- `_management_filters.html`  
  Filter khusus halaman manajemen data (mirip preview, plus aksesoris bulk by filter).
- `_management_insert_form.html`  
  Form tambah data tunggal dari halaman manajemen.
- `_management_table.html`  
  Tabel CRUD manajemen data (mobile + desktop), checkbox, edit/delete row.
- `_management_bulk_modal.html`  
  Modal bulk update + konfirmasi aksi + form hidden untuk bulk delete.
- `_script_upload_period_format.html`  
  JS helper untuk format validasi input `period_date` menurut `time_period`.
- `_script_preview_filters.html`  
  JS untuk reset/filter preview, shortcut, dan pengaturan limit.
- `_script_management_bulk_actions.html`  
  JS bulk action (pilih baris, confirm, update, delete), edit modal, dan sinkron state checkbox.
- `_aggregated_period_form.html`  
  Form analisis periode agregat (indikator dan rentang period).
- `_aggregated_plot_form.html`  
  Form request grafik line.
- `_script_aggregated_analysis.html`  
  JS untuk generate plot (Plotly), render table pivot periodik, dan export analisis period.
- `_data_type_badge.html`  
  Badge flow/stock.
- `_time_period_badge.html`  
  Badge monthly/quarterly/yearly.
- `_empty_state.html`  
  State tampilan saat tidak ada data.
- `_pagination.html`  
  Komponen pagination reusable untuk preview dan manajemen.
- `_script_theme_toggle.html`  
  Toggle tema terang/gelap (persist ke localStorage).

## Aturan pakai cepat

- Untuk perubahan UI global, cek `base_tailwind.html` dulu.
- Untuk perubahan perilaku halaman, cek partial yang dipakai lewat `{% include ... %}` di halaman target.
