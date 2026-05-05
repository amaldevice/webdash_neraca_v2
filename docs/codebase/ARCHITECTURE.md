# Arsitektur Aplikasi

## Tujuan

Aplikasi adalah repository data BPS berbasis Flask yang memfokuskan fungsi ke:

- ingest data (upload file/Manual Input),
- validasi + normalisasi data,
- manajemen CRUD data,
- analisis perbandingan periode (M/M, Q/Q, Y/Y, YTD, C/C),
- ekspor data mentah/hasil analisis.

## Komponen Utama

### 1) Ingress Layer

- `routes/upload_routes.py`
  - `POST /upload` menerima file Excel.
- `routes/upload_routes.py`
  - `POST /upload/manual` untuk input manual.
- CSRF + session + rate-limit di jalur upload.

### 2) Application Layer

- `app.py`
  - app factory + config bootstrap + filter `to_wita`.
- `config.py`
  - env resolution, security defaults, upload limits, secret rules.

### 3) Domain Layer (Services)

- `services/upload_flow.py`: orkestrasi upload, duplicate handling, confirm/overwrite/skip.
- `services/upload_preview.py`: cache preview berbasis disk agar multi-worker konsisten.
- `services/manual_entries.py`: normalisasi input manual.
- `services/template_service.py`: generate template dataset-aware.
- `excel_parser/*`: parsing Excel, deteksi layout horizontal/vertical/mixed.
- `services/charts.py`, `services/period_*`: transform data untuk UI/analisis.
- `services/raw_export.py`: export CSV/Excel.

### 4) Data Layer

- `infrastructure/db.py`
  - inisialisasi engine dan `scoped_session`.
- `infrastructure/orm_models.py`
  - `DataEntry` + `UploadRun`, constraint unik termasuk `dataset_code`.
- `models/queries.py`
- `models/mutations.py`
- `models/data_filters.py`

## Arus Data

### Alur Upload

1. File masuk endpoint upload.
2. CSRF dan rate limit divalidasi.
3. Parser mencoba mode long-format dataset-aware lalu fallback horizontal/vertical.
4. Parser mengembalikan payload, warnings, duplicate candidates, summary.
5. Preview disimpan di session/disk (`_preview_sessions` + file cache).
6. User konfirmasi → `persist_upload_entries` + optional overwrite plan.
7. Menulis `data_entries` + mencatat `upload_runs`.

### Alur Manual

1. Form manual diparsing (`build_manual_entry`).
2. `parse_period_date` menerapkan fleksibilitas marker `YYYY`, `YYYY-MM`, `YYYY-Qn`.
3. Validasi metadata/time series lalu `insert`.

### Alur Analisis & Ekspor

1. Filter di route dashboard diteruskan ke query period.
2. Perhitungan growth dilakukan di `period_comparison_calculators` (pure math).
3. Hasil dirender JSON/table atau diekspor lewat `period_analysis_workbook`.

## Kontrak Data yang Kritis

- `DataEntry` menyimpan:
  - `uploader_name`, `version`, `template_type`, `data_type`, `time_period`,
  - `indicator_name`, `value`, `unit`, `region_code`,
  - `year`, `month`, `quarter`, `dataset_code`.
- Unik constraint runtime utama di DB:
  - `uploader_name + version + indicator_name + year + month + quarter + dataset_code`.
- Duplicate warning pre-check memakai key indikator+periode (terlihat seperti "warning"), sedangkan overwrite final mengikuti unik DB.

## Keputusan Arsitektur Penting

- Preview cache disk untuk menghindari kehilangan state pada worker/process paralel.
- Parser dipisah dari routing agar logic testable.
- Template dan parser dataset-aware dibangun di service, bukan hardcoded di template.
- Fitur agregasi summary lama sudah didepresiasi; fokus data repository murni.

