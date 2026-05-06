# Domain Context: Documentation (global)

## Lingkup
Buku pegangan untuk perilaku aplikasi web internal pengelolaan data BPS: unggah template Excel (dataset-aware), input manual, validasi/normalisasi, manajemen data (`data_entries`), filter rentang periode, dan ekspor data mentah.

## Kosakata wajib
- `dataset_code`: identifier dataset aktif (mis. `pinjaman`, `simpanan`, `atm`). Kunci partisi data.
- `dataset_slug`: slug string untuk URL/template parser.
- `source_sheet`: nama sheet Excel sumber yang dipakai parser.
- `data_type`: mode periode (`monthly`, `quarterly`, `yearly`).
- `time_period`: nilai periode manusiawi pada baris unggah/input.
- `uploader_name`: pemilik metadata upload/manual.
- `version`: versi dataset yang dipilih saat unggah.
- `period marker`: `start_period` / `end_period` pada halaman filter, tetap diterapkan ke preview, manajemen, dan ekspor.
- `upload_runs`: entri kontrol jalannya import (status + timing + error ringkas).

## Arsitektur ringkas
- Flask app (`app.py`) mengatur route dan orchestration request.
- Parser/upload memakai `excel_parser/*`, `services/upload_flow.py`, `services/upload_preview.py`.
- Penyimpanan utama di tabel `data_entries`, dipandu helper model di `models/` dan migrasi `alembic/`.
- Dashboard memakai `models/queries.py` untuk query data dengan filter periode.
- Ekspor lewat endpoint `/export` dengan filter aktif.

## Aturan proses
- Gunakan mode dataset-aware jika fitur berkaitan dengan `/upload` dan pemetaan dataset.
- Prioritaskan konsistensi perilaku antar halaman: filter periode harus konsisten dari preview, data-management, dashboard, hingga export.
- Deteksi duplikasi awal (indikator + periode) hanya warning; pencegahan overwrite tetap mengikuti unique key DB.
- Baca dan ikuti aturan di [`.cursor/rules/planning-&-executing-sync.mdc`](../.cursor/rules/planning-&-executing-sync.mdc) saat perubahan perilaku/fungsional.

## Keputusan penting
- Migrasi `dataset_code` bersifat fase; lihat `docs/README_DOCS.md` untuk langkah migrasi + backfill.
- Template unggah dipersepsi panjang sebagai long-format; pemetaan header tetap disesuaikan ke `dataset_code`.
