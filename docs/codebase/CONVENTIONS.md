# Konvensi Kode dan Praktik

## Struktur Aplikasi

- `routes/*`: endpoint HTTP + input parsing ringan + pemanggilan service.
- `services/*`: orchestration bisnis (upload, parse, preview, filter, chart, analisis).
- `models/*`: query/mutation/filter dan kontrak data.
- `infrastructure/*`: koneksi DB, ORM, query optimization by dialect.
- `excel_parser/*`: parsing & normalisasi format Excel terpisah dari model.
- Utility scripts di `scripts/*` dipisah dari runtime app.

## Gaya Kode

- Kembali ke modul yang spesifik dan kecil; beberapa file besar dipotong menjadi submodules sebelumnya.
- Gunakan `dataclass`/typed return object untuk response flow (contoh `UploadFlowResponse`).
- Fungsi dan modul diberi nama domain (`parse_period_date`, `build_upload_response`, `persist_upload_entries`).
- Hindari aliasing berlebihan; path dan konfigurasi dipusatkan di `config.py`.

## Konvensi Validasi & Error

- Validasi input ada di layer service/form:
  - tipe file (`allowed_file`) + metadata required (`uploader_name`, `version`, dsb),
  - parser-level checks (`invalid_rows`, warnings),
  - fallback period parser untuk format fleksibel.
- Response preview sengaja menampilkan warning terstruktur, bukan silent fail.
- Error user-facing disalurkan lewat flash message; error internals tetap ke logging.

## Konvensi Keamanan

- Upload route mengaktifkan CSRF token check.
- Session cookies:
  - `HttpOnly`, `Samesite`, dan `Secure` sesuai env.
- App factory blok start production bila `FLASK_ENV=production` tanpa DSN eksplisit.
- Preview session memakai file di `UPLOAD_FOLDER` dengan prefix khusus untuk menghindari konflik antar session.

## Konvensi DB

- Semua operasi data utama melalui `scoped_session` di `infrastructure/db.py`.
- `insert`/`bulk`/`upsert` dipusatkan di `models/mutations.py`.
- Filtering/query dirangkum agar endpoint tidak melakukan SQL mentah.
- Dialect-aware upsert di `infrastructure/dialect_upsert.py`.

## Konvensi Nama & Waktu

- Timezone dan format waktu WITA dipusatkan (`services/timeutil.py`).
- `version` memakai timestamp WITA otomatis (upload dan manual).
- `dataset_code` diwajibkan untuk upload/input jika mode dataset-aware diaktifkan.

## Konvensi UI

- Template memakai partials di `templates/partials/` (form, table, script, alert).
- Komponen visual dijaga konsisten lintas halaman: preview + data-management.
- Paginasi dan filter state menjaga kebugaran URL (query param persist).

