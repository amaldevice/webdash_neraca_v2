# Refactor Plan: Upload/Input + Template per Sheet (Upload dan Manual Input)

## Ringkasan Tujuan

Membangun alur data berbasis **dataset per sheet** dari `REKAP Bank indonesia_rev.xlsx` agar user memilih target data set terlebih dahulu, lalu:

- **Upload Excel**: user dapat mengunduh template yang sesuai dataset, isi data, lalu upload.
- **Input Manual**: form manual juga dibatasi sesuai dataset agar schema konsisten.
- **Persistensi**: setiap row tersimpan dengan label dataset (untuk dedup, pelacakan versi, query, dan audit per dataset).

Output utama: satu sistem upload/input yang reusable, tidak tergantung struktur sheet tunggal.

## Ruang Lingkup

- Kecualikan sheet: `Resume`, `PMSE`, `Perkembangan Indikator`.
- Fokus awal: refactor alur upload/manual/template + penyimpanan, tidak mengubah engine SQLAlchemy yang sudah ada.
- Semua perubahan harus mempertahankan UX saat ini sambil menambah wizard pemilihan dataset.

## Temuan Eksplorasi Sheet (awal)

Klasifikasi dan template referensi wajib **hanya dari** sumber berikut:

- File Excel master: `D:/webdash_neraca/REKAP Bank indonesia_rev.xlsx`
- Arah eksplorasi harus mengikuti struktur header aktual di file ini. Template tidak boleh diciptakan dari asumsi eksternal.

Klasifikasi yang dipakai untuk perencanaan:

### Dikecualikan

- `Resume` → Two Way
- `PMSE` → Two Way (khusus panel komposit)
- `Perkembangan Indikator` → Empty / non-data

### Diproses di Refactor Utama

- `pinjaman` → **Three Way**  
  Struktur long: `kelompok_bank` + `kelompok_pinjaman` + `lapangan_usaha` + periode
- `simpanan` → **Three Way**  
  Struktur long: `kelompok_jenis_simpanan` + `produk_simpanan` + `rentang_nominal` + periode
- `ecommerce` → **Two Way**  
  Struktur long: `metode_pembayaran` + `tahun` + `triwulan` (1–4) + nilai
- `ATM` → **Two Way**  
  Struktur long: `jenis_transaksi` + `jenis_nilai` (`volume`|`nominal`) + `tahun` + `bulan` + nilai
- `Kartu kredit ` → **Two Way**  
  Struktur long: sama seperti `ATM`
- `UANG ELEKTRONIK` → **Two Way**  
  Struktur long: sama seperti `ATM` (banyak periode kosong di sheet asli)
- `Indikator sekda BI` → **Three Way**  
  Struktur long: `no_urut` (opsional) + `indikator` + `subindikator` + `satuan` + periode

### Catatan waktu & growth dalam data source

- File sumber mencampur skenario:
  - nilai mentah (periodik tunggal),
  - pertumbuhan M to M,
  - pertumbuhan Q to Q,
  - pertumbuhan Y to Y,
  - bagian/baris yang hanya sebagian berisi data.
- Untuk DB, pola yang aman adalah **long-format dengan dimensi metrik**:
  - Satu baris DB = satu observasi `(dataset, dimensi utama, metric_name, year, month/quarter, value)`.
  - `metric_name` wajib menyimpan tipe angka, contoh: `realisasi`, `m2m_growth`, `q2q_growth`, `y2y_growth`.
  - Untuk growth yang tidak ada di baris tertentu → row tidak dibuat, tetap rekam status parse sebagai warning (`source_sheet`, `missing_metric`, `row_index`).
- Partial data tetap diimpor jika valid di `metric_name + period` yang tersedia; baris yang tidak lengkap akan:
  - di-skip dengan pesan warning jika `value` kosong,
  - atau diimport sebagai baris dengan `value` kosong hanya bila policy khusus diset `allow_blank_value` (default `false`).
- Tambahkan field metadata run-level:
  - `source_sheet`, `raw_period_label`, `ingest_profile` (full/partial/growth-only) untuk audit kualitas.

### Contoh template per sheet (long format, header + 2 baris contoh)

Header dan angka contoh **disamakan** dengan sel aktual `REKAP Bank indonesia_rev.xlsx` (bukan placeholder): wide sheet memadukan **total tahun** (kolom tunggal per tahun) dan **runtutan bulan** mulai blok 2022 untuk `pinjaman`; template long memakai pasangan `(tahun, bulan)` numerik agar parser stabil (`bulan` = 1–12). File Excel gabungan yang bisa diunduh/diserahkan ke user: `static/templates/rekap_dataset_long_templates.xlsx` (dibangun ulang dengan `python scripts/build_rekap_long_templates.py`).

#### `pinjaman`
| kelompok_bank | kelompok_pinjaman | lapangan_usaha | tahun | bulan | metric_name | nilai |
| --- | --- | --- | --- | --- | --- | --- |
| Bank Pemerintah dan Bank Pembangunan Daerah | Pinjaman Berdasarkan Lapangan Usaha | Pertanian, Kehutanan & Perikanan | 2022 | 4 | realisasi | 993372.628453 |
| Bank Pemerintah dan Bank Pembangunan Daerah | Pinjaman Berdasarkan Lapangan Usaha | Pertambangan Dan Penggalian | 2022 | 4 | realisasi | 16050.265891 |

> Catatan hierarki kolom A sheet asli: baris tebal = `kelompok_bank`; anak langsung seperti *Pinjaman Berdasarkan Lapangan Usaha* = `kelompok_pinjaman`; baris sektor detail = `lapangan_usaha`. Baris agregat antar-bank mengikuti pola yang sama.

#### `simpanan`
| kelompok_jenis_simpanan | produk_simpanan | rentang_nominal | tahun | bulan | metric_name | nilai |
| --- | --- | --- | --- | --- | --- | --- |
| Rupiah | Giro | 0 - 10 juta | 2022 | 1 | realisasi | 8865.261165 |
| Rupiah | Giro | > 10 - 100 juta | 2022 | 1 | realisasi | 48297.513338 |

> Sheet asli punya rantai **Rupiah → Giro → rentang nominal**; tanpa kolom `produk_simpanan` (mis. Giro) pemetaan ke DB akan ambigu.

#### `ecommerce`
| metode_pembayaran | tahun | triwulan | metric_name | nilai |
| --- | --- | --- | --- | --- |
| COD/Tunai | 2020 | 1 | realisasi | 10679.82 |
| e-Money | 2021 | 2 | realisasi | 28800.43 |

> `triwulan` = 1–4 setara Tw I–Tw IV pada header wide BI.

#### `ATM` / `Kartu kredit ` / `UANG ELEKTRONIK`
| jenis_transaksi | jenis_nilai | tahun | bulan | metric_name | nilai |
| --- | --- | --- | --- | --- | --- |
| Tunai | volume | 2018 | 9 | realisasi | 487354 |
| Tunai | nominal | 2018 | 9 | realisasi | 338447.94678296254 |

Contoh **`Kartu kredit `** (nama sheet sumber ada spasi di akhir):

| jenis_transaksi | jenis_nilai | tahun | bulan | metric_name | nilai |
| --- | --- | --- | --- | --- | --- |
| Tunai | volume | 2018 | 9 | realisasi | 254 |
| Tunai | nominal | 2018 | 9 | realisasi | 309.71613361920623 |

Contoh **`UANG ELEKTRONIK`** (nilai diambil dari kolom yang terisi di sheet; banyak sel awal kosong):

| jenis_transaksi | jenis_nilai | tahun | bulan | metric_name | nilai |
| --- | --- | --- | --- | --- | --- |
| BELANJA | volume | 2019 | 10 | realisasi | 117427 |
| BELANJA | nominal | 2019 | 10 | realisasi | 7457.595445711226 |

> Kolom `jenis_nilai` memisahkan pasangan **Volume/Nominal** yang di sheet asli ada di kolom B; `metric_name` tetap `realisasi` untuk angka level (growth lain tetap mengikuti enum `metric_name` di atas).

#### `Indikator sekda BI`
| no_urut | indikator | subindikator | satuan | tahun | bulan | metric_name | nilai |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | Simpanan | - Giro | Rp. Juta | 2010 | 1 | realisasi | 300933 |
|  | Simpanan | - Tabungan | Rp. Juta | 2010 | 1 | realisasi | 875826 |

> `bulan` numerik 1–12 selaras header bulan Indonesia di baris time wide; `subindikator` pertahankan awalan `- ` seperti teks BI.

## Desain Target

### 1) Katalog dataset

Buat modul baru `services/dataset_catalog.py`:

- Source of truth daftar dataset yang diizinkan.
- Setiap dataset punya metadata:
  - `slug`: kunci internal (e.g. `pinjaman`, `indikator_sekda_bi`)
  - `label`: nama manusia
  - `source_sheet`: nama sheet di Excel
  - `table_type`: `one_way|two_way|three_way`
  - `time_period_mode`: `monthly|quarterly|yearly`
  - `required_template_headers`: daftar kolom template long-format
  - `manual_form_fields`: field yang tampil di input manual
  - `template_mode`: `long` (rekomendasi) + optional mode khusus
  - `enabled_for_upload`: true/false
  - `enabled_for_manual`: true/false

### 2) Pelayan template dinamis

Buat modul baru `services/template_service.py`:

- `generate_workbook_for_dataset(dataset_slug, *, with_sample=True, include_notes=True)`
- `build_template_file_response(dataset_slug)` (Flask `Response`)
- `template_cache_key(dataset_slug, version)` untuk cache optional.
- Template format default: **long format** (baris tunggal = satu observasi) agar parser seragam.
- Endpoint unduh template wajib didahului pemilihan dataset:
  - `GET /upload/template/<dataset_slug>` hanya valid bila `dataset_slug` sudah dipilih.
  - Jika dipanggil tanpa dataset: tampilkan instruksi tegas `Pilih dataset/tabel dulu`.

### 3) Flow pemilihan sumber → dataset → action

Perubahan route/form:

- `GET /upload`:
  1. pilih mode (`upload` | `manual`)
  2. pilih dataset (dari katalog; tanpa tiga sheet yang dikecualikan)
  3. untuk mode upload tampil tombol unduh template dataset
  4. untuk mode manual tampil form sesuai dataset
- `POST /upload`:
  - jika mode upload: validasi pilihan dataset, parse sheet `source_sheet`, lalu lanjut preview.
  - jika mode manual: validasi dataset lalu simpan via helper manual dataset-aware.

### 4) Parser + validasi data aware-dataset

Modifikasi `excel_parser/payload.py`:

- `parse_excel_payload(..., sheet_name: str | None = None, dataset_slug: str | None = None, template_shape: str = "long")`
- `dataset_slug` wajib untuk flow yang memilih dataset; jika kosong dan bukan mode legacy: reject dengan error jelas.
- Deteksi layout diperketat: menolak format yang tidak sesuai header template dataset.
- Normalisasi kolom wajib:
  - `year`, `month`/`quarter`, `value`, `label dimensions` sesuai katalog.

### 5) Persistence dan audit

- Tambah kolom dataset di `data_entries`:
  - `dataset_code` (nullable sementara saat transisi, nanti non-null setelah backfill)
- Unique key diperluas:
  - `uploader_name + version + dataset_code + indicator_name + year + month + quarter`
- Tambah table audit `upload_runs` untuk provenance upload:
  - `id, run_id, dataset_code, source_sheet, uploader_name, template_code, file_hash, rows_total, rows_inserted, rows_skipped, duplicate_count, started_at, finished_at, status, error_summary`
- Tambah helper/constraints migrasi untuk mapping dataset old rows tanpa kode dataset (fallback default dataset map by heuristik sementara).

### 6) UI/UX dan template per dataset

- `templates/upload.html` + partial:
  - tahap 1/2/3 (mode, dataset, action)
  - preview tetap menampilkan ringkasan konflik + duplicate.
- Template auto:
  - `templates` diunduh per dataset dengan tab/format yang sama style-nya untuk consistency.
  - header minimal + 1–2 sample baris contoh.

## Rencana Implementasi (beruntun)

### Fase 0 — Penguncian kontrak & baseline

- [x] Simpan matriks dataset final (nama sheet, tipe, template schema, mode waktu).
- [x] Freeze fitur legacy upload manual tanpa dataset selection sebagai jalur kompatibilitas sementara.
- [x] Tambah tes parser untuk `sheet_name/dataset_slug` required.

### Fase 1 — Foundation catalog/template service

- [x] Buat `services/dataset_catalog.py` + fixture untuk daftar 7 dataset aktif.
- [x] Buat `services/template_service.py` dengan generator long-format per dataset.
- [x] Tambah command/helper generate template smoke test (`tests/test_dataset_catalog.py`, `tests/test_template_service.py`, `scripts/build_rekap_long_templates.py`).

### Fase 2 — Refit route/wizard

- [x] Refactor `routes/upload_routes.py` ke multi-step flow.
- [x] Inject catalog ke context upload page.
- [x] Tambah endpoint template download per dataset: `/upload/template/<dataset_slug>`.
- [x] Batasan: `Resume`, `PMSE`, `Perkembangan Indikator` tidak muncul di UI selection.

### Fase 3 — Parser + manual data path

- [x] Update `excel_parser/payload.py` untuk dataset-aware parsing.
- [x] Update `services/upload_flow.py` agar menggunakan dataset context di parsing + duplicate checks.
- [x] Update `services/manual_entries.py`/flow manual agar mengisi `dataset_code`.
- [x] Update preview context untuk menampung schema dataset di kandidat duplikasi (`upload_preview`, `preview_duplicates_batches`, metadata sesi).

### Fase 4 — Persistence layer

- [x] Migrate `data_entries` tambah `dataset_code`, indeks unik baru + constraint migration fallback (`alembic/versions/002_dataset_code_upload_runs.py`).
- [x] Tambah `upload_runs` + helper tulis audit (`services/upload_runs.py`, `record_upload_run` dari alur upload sukses/konfirmasi).
- [x] Sesuaikan `models/mutations.py`/`dialect_upsert` agar insert/upsert mengisi `dataset_code`.
- [x] Update query/pagination/filter agar bisa filter dataset dari list UI (`data_filters`, `list_view`, partials preview/management).

### Fase 5 — Validasi & compatibility

- [x] Tes unit parser long-format untuk semua slug katalog (`tests/test_dataset_long_parse.py` + template `generate_workbook_for_dataset`).
- [x] Tes e2e Playwright: smoke unggah + pratinjau (`tests/e2e/smoke.spec.ts`, berkas `static/e2e_agent_browser.xlsx`).
- [x] Tes regresi legacy: wide horizontal tanpa slug (`test_parse_legacy_horizontal_without_dataset_slug`).
- [x] Migration rehearsal (dokumen): `docs/README_DOCS.md` → bagian **Migrasi & rehearsal `dataset_code`** (backup, backfill ilustratif, verifikasi unik).

### Fase 6 — Rollout

- [x] Dokumentasi UX singkat: `docs/README_DOCS.md` → **Panduan: unggah Excel & dataset** (wizard, `REQUIRE_DATASET_FOR_UPLOAD`, rollback).
- [x] Gate produksi: tetap via env `REQUIRE_DATASET_FOR_UPLOAD=1` (default aplikasi legacy-friendly; panduan mendorong set di kantor).
- [x] Checklist produksi / smoke browser: `scripts/agent_browser_upload_smoke.ps1` + verifikasi manual `agent-browser` ke `/upload`.

## Risiko + Mitigasi

- Risiko: deteksi header yang salah untuk dataset 2-way vs 3-way.  
  Mitigasi: sertakan validasi header wajib dan error “schema not matched”.
- Risiko: data lama tanpa `dataset_code` karena transisi.  
  Mitigasi: backfill + constraint bertahap (nullable dulu, lalu tighten).
- Risiko: template long-format membingungkan user lama yang biasa template wide.  
  Mitigasi: sediakan sample contoh 2 baris + FAQ singkat di halaman unduh.
- Risiko: growth metrics (M2M/Q2Q/Y2Y) kehilangan konteks saat normalisasi.  
  Mitigasi: wajib simpan `metric_name` sebagai dimensi dan map ke enum `realisasi|m2m_growth|q2q_growth|y2y_growth`.
- Risiko: manual path terbagi dan rentan regresi.  
  Mitigasi: route-level tests + fixture per dataset.

## Verifikasi Eksekusi

Per run sebelum checkpoint:

- `python -m pytest tests/test_upload_flow.py`
- `python -m pytest tests/test_excel_parser.py`
- `python -m pytest tests/test_browse_summary_sqlalchemy.py` (jika filter dataset ditambahkan ke browse path)
- `python -m pytest tests/simple_tests/functional_tests/test_landing_page.py tests/simple_tests/functional_tests/test_data_visualization.py` (jika halaman baru ditambah)
- smoke Playwright untuk:
  - wizard dataset,
  - download template,
  - preview upload,
  - simpan & daftar filter dataset.

## Output Dokumen

- `docs/superpowers/plans/2026-04-16-dataset-aware-upload-manual-refactor.md` (dokumen ini)
- `docs/superpowers/plans/2026-04-16-rekap-sheet-table-type-and-template-mapping.md` (matriks sheet + header long)
- `static/templates/rekap_dataset_long_templates.xlsx` + `scripts/build_rekap_long_templates.py`
- `docs/README_DOCS.md` (indeks + changelog + panduan unggah/migrasi); `docs/planning.md` (stub sinkron Cursor)
- `.cursor/plans/bps_data_management_system_bd94389d.plan.md` (status task YAML, ikut Git)
