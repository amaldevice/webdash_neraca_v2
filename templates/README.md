# templates/

Bagian UI berbasis Jinja2 untuk aplikasi.

## Template Utama

- `base_tailwind.html`
  - Layout utama (topbar, flash, wrapper halaman, footer).
  - Menyatukan font, style (`/static/css/tailwind.css`, `/static/css/style.css`), dan toggle tema.
- `landing.html`
  - Dashboard ringkasan awal (cards + call-to-action).
- `upload.html`
  - Halaman input (`upload` dan `manual`) dengan `mode`.
- `preview.html`
  - Pratinjau data terfilter, pagination, dan tombol export.
- `data_management.html`
  - Area CRUD lengkap: filter, insert, tabel, bulk action, modal edit.
- `dashboard.html`
  - Menampilkan metrik repository dan analisis periode (rute terpisah).

## Subfolder

- `partials/`  
  Kumpulan komponen dan script kecil yang dipakai lintas halaman untuk menghindari duplikasi.  
  Lihat juga: `templates/partials/README.md`.

## Alur Integrasi

- Route backend (`app.py`) me-render template ini dengan context:
  - `summary`, `entries`, `filters`, `filter_options`, `pagination` data.
- Perubahan endpoint harus diikuti penyesuaian include di template yang relevan agar payload/filter tetap sinkron.
