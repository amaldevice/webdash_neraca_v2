# Sistem Data BPS

> Aplikasi web internal berbasis Flask + SQLite untuk mengelola data BPS dari template Excel maupun input manual, melakukan normalisasi, menyusun metrik repository, dan menyediakan dashboard bertingkat dengan filter serta ekspor data mentah yang konsisten.

**State proyek, peta `docs/`, unggah/dataset, migrasi, changelog:** baca **[docs/README_DOCS.md](docs/README_DOCS.md)** — gabungan ringkas dokumen operasional; stub sinkron [`docs/planning.md`](docs/planning.md); plan Cursor (YAML todos) di **[`.cursor/plans/bps_data_management_system_bd94389d.plan.md`](.cursor/plans/bps_data_management_system_bd94389d.plan.md)** (ikut Git).

## Langkah Cepat (1-3 Langkah)

1. Lakukan kloning repositori dan masuk ke direktori proyek.
2. Instal ketergantungan menggunakan `pip` atau `uv pip`.
3. Inisialisasi basis data, lalu jalankan aplikasi pada `http://127.0.0.1:5000`.

## Instalasi (pip)

```bash
git clone <repo-url>
cd webdash_neraca
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -c "from models import init_db; init_db()"
npm install
npm run build:css
python app.py
```

## Instalasi (uv pip)

```bash
git clone <repo-url>
cd webdash_neraca
python -m pip install uv
uv venv .venv
.\.venv\Scripts\activate
uv pip install -r requirements.txt
python -c "from models import init_db; init_db()"
npm install
npm run build:css
python app.py
```

## Skema basis data (Alembic)

Untuk lingkungan yang memakai **SQLAlchemy** (`DATABASE_URL` di-set), terapkan migrasi:

```bash
rtk python -m alembic upgrade head
```

Urutan pemilihan DSN migrasi: `ALEMBIC_DATABASE_URL` (opsional) → `DATABASE_URL` → bawaan `sqlite:///<folder proyek>/data.db`.

Bila MySQL memunculkan **`Unknown column 'dataset_code'`** atau **`Table 'data_entries' already exists`** saat migrasi, ikuti [docs/troubleshooting/mysql-schema-dataset-code-and-alembic.md](docs/troubleshooting/mysql-schema-dataset-code-and-alembic.md) dan skrip `python scripts/apply_dataset_code_migration.py --dry-run` / `--yes`.

Instalasi legacy tanpa `DATABASE_URL` tetap boleh memakai `python -c "from models import init_db; init_db()"` sampai strangler menggantikan penuh.

### Contoh `DATABASE_URL` (SQLAlchemy)

| Dialek | Contoh nilai |
|--------|----------------|
| **SQLite** (berkas) | `sqlite:////var/lib/app/data.db` atau `sqlite:///C:/app/data.db` |
| **MySQL 8** | `mysql+pymysql://user:password@host:3306/dbname?charset=utf8mb4` — butuh paket **PyMySQL** (sudah di `requirements.txt`). |
| **PostgreSQL** | `postgresql+psycopg://user:password@host:5432/dbname` — butuh **psycopg** (mis. `pip install "psycopg[binary]"` dari `requirements-dev.txt`). |

Setelah DSN di-set, jalankan migrasi: `python -m alembic upgrade head`. Smoke integrasi MySQL/PostgreSQL: jalankan `pytest tests/integration/` di mesin yang punya `DATABASE_URL` non-sqlite dan skema sudah `alembic upgrade head` (lihat `tests/integration/test_remote_dialect_smoke.py`).

### Migrasi data SQLite → server SQL (sekali jalan)

Skrip: `scripts/migrate_sqlite_to_mysql.py` (target URL boleh MySQL/MariaDB atau PostgreSQL lewat SQLAlchemy).

1. Terapkan skema di target: `alembic upgrade head` dengan `DATABASE_URL` / `MIGRATE_TARGET_URL` mengarah ke server tujuan.
2. Uji baca saja: `python scripts/migrate_sqlite_to_mysql.py --dry-run` (opsional set `MIGRATE_TARGET_URL`).
3. Muat penuh (biasanya kosongkan dulu): `python scripts/migrate_sqlite_to_mysql.py --truncate-target --target-url "mysql+pymysql://..."` atau set env `MIGRATE_TARGET_URL` / `MYSQL_TARGET_URL` dan `SQLITE_SOURCE_PATH` ke file `.db` sumber.

Skrip memverifikasi jumlah baris dan `SUM(value)` pada `data_entries` setelah selesai.

### Backup data SQL → SQLite untuk cadangan

Skrip: `scripts/migrate_mysql_to_sqlite.py`

1. Set DSN sumber (MySQL/PostgreSQL): `--source-url` atau env `MYSQL_SOURCE_URL` / `MYSQL_TARGET_URL` / `MIGRATE_TARGET_URL` / `DATABASE_URL` (non-sqlite).
2. Jalankan dry-run dulu: `python scripts/migrate_mysql_to_sqlite.py --dry-run`.
3. Backup penuh ke file default: `python scripts/migrate_mysql_to_sqlite.py`  
   (default akan menulis ke `backups/data_backup_<YYYYMMDD_HHMMSS>.db`).
4. Atau backup ke lokasi tertentu: `python scripts/migrate_mysql_to_sqlite.py --sqlite-path "D:/backup/webdash.db"`.
5. Untuk menulis ke target yang sudah ada: gunakan `--truncate-target` (replace) atau `--append`.

Skrip memverifikasi jumlah baris dan `SUM(value)` antara sumber dan target setelah copy.

Catatan keamanan: file backup SQLite hasil copy adalah snapshot data; lakukan `chmod`/izin akses minimum pada server.

## Fitur

### Fitur Inti
- [x] **Portal beranda (landing page)**: Menyediakan metrik ringkas repository, metadata penting, dan akses cepat untuk unggah serta input manual.
- [x] **Dua jalur masuk data**: Parser Excel mendukung template horizontal dan vertikal, sedangkan input manual tetap memaksa keterisian metadata secara konsisten.
- [x] **Metrik singkat repository**: Menampilkan ringkasan indikator aktif, rentang periode, dan jumlah baris dari data aktif.

### Fitur Tambahan
- [x] **Penyaringan rentang periode**
  - Halaman **Preview-Data** dan **Data-Management** menggunakan parameter `start_period` + `end_period`.
  - Halaman **Dashboard** menggunakan parameter `period_start` + `period_end` untuk grafik/analisis, serta `start_period` + `end_period` untuk filter rentang yang konsisten.
  - Semua fitur filter ini berlaku untuk proses ekspor dan analisis agar hasil yang ditampilkan konsisten dengan ruang lingkup waktu yang dipilih.
- [x] **Penelusuran tabel terfilter**: Mendukung paginasi dan pembatasan jumlah data per halaman, dengan tampilan baris/tabel yang konsisten.
- [x] **Ekspor data mentah**: Menyediakan unduhan CSV/Excel melalui `/export` dengan mempertahankan parameter filter aktif.
- [x] **Validasi metadata**: Memastikan atribut seperti `uploader`, `version`, `data_type`, dan `time_period` tervalidasi sejak proses unggah/input.
- [x] **Aksi massal**: Halaman Data-Management menyediakan pembaruan massal, penghapusan massal, dan penghapusan berbasis filter.
- [x] **Alur analisis periode**: Halaman Dashboard mendukung analisis M to M, Q to Q, Y to Y, YTD, dan C to C, serta ekspor hasil analisis ke Excel.
- [x] **Deteksi duplikasi lintas unggah/manual**: Sistem menandai konflik awal berdasarkan kunci indikator + periode (`indicator_name`, `year`, `month`, `quarter`), sekaligus tetap menjaga penyimpanan berdasarkan unique key database.

### Catatan penting: warning bukan berarti overwrite otomatis
- Deteksi awal dan penyimpanan memakai kunci yang berbeda.
- Deteksi awal menandai konflik jika indikator + periode sama, untuk memberi sinyal di preview (termasuk kasus lintas `uploader` dan `version`).
- Penyimpanan akhir tetap mengikuti unique constraint DB `uploader + version + indicator + year + month + quarter`.
- Contoh praktis:
  - Data existing: `uploader=A`, `version=v1`, `indicator=GDP`, `2024-03`.
  - Upload baru: `uploader=B`, `version=v2`, `indicator=GDP`, `2024-03`.
  - Hasil: muncul warning karena indikator+periode cocok, namun tetap akan disimpan sebagai baris baru karena kombinasi unik DB berbeda.
- Overwrite/replace terjadi hanya saat kombinasi unik DB persis sama.

### FAQ cepat: duplikasi upload/manual
- **Q: Kenapa upload saya dapat warning duplikasi tapi tetap berhasil disimpan?**
  - **A:** Warning muncul dari pengecekan awal indikator+periode. Jika `uploader`/`version` berbeda, data tetap dianggap berbeda oleh constraint unik dan disimpan sebagai baris baru.
- **Q: Kapan warning berarti data akan ditimpa?**
  - **A:** Saat kombinasi unik `uploader + version + indicator + year + month + quarter` benar-benar sama, maka proses simpan akan menimpa data lama (overwrite) sesuai mode konfirmasi.
- **Q: Kenapa saya harus waspada jika warning muncul?**
  - **A:** Karena warning memberi konteks bahwa indikator+periode sudah ada di sistem; jika unique key juga sama, tindakan simpan bisa mengganti data sebelumnya.

### Cara baca template Excel: vertikal vs horizontal
- Pada format **vertikal**, setiap baris mewakili satu periode. Karena itu `periode` biasanya muncul sebagai kolom eksplisit (contoh: `periode`, `2026-01`, `2026-02`, dst.).
- Pada format **horizontal**, `periode` diperlakukan sebagai label judul header, sementara tiap baris mewakili satu indikator. Karena itu kolom pertama baris data berisi nama indikator (`Contoh_Bunga`, `Contoh_Inflasi`, ...), dan header kolom di kanan berisi periode (`2026-01`, `2026-02`, dst.).
- Akibatnya contoh:
  - `periode	2026-01	2026-02	...`
  - `Contoh_Bunga	125000	131200	...`
  - `Contoh_Inflasi	2.5	2.7	...`
  adalah perilaku yang normal untuk template horizontal; sel `periode` di `A1` diperlakukan sebagai label baris header, bukan kolom data terpisah.

### Ringkasan Berkas Python

- `app.py`: Fabrikasi app Flask dan route utama aplikasi.
- `aggregator.py`: Dihapus; fitur agregat dan cache ringkas tidak lagi dipakai.
- `excel_parser.py` (legacy): Modul parser lama (masih tetap dipertahankan untuk kompatibilitas).
- `models.py` (legacy): Entrypoint kompatibilitas untuk paket `models/`.
- `models/`: Paket model utama (`connection`, `queries`, `mutations`, `browse`, `data_filters`).
- `infrastructure/orm_models.py`: Model SQLAlchemy 2.0 (mirror skema); `alembic/` + `alembic.ini` untuk migrasi.
- `services/aggregation.py`: Dihapus. Metrik dihitung dari data aktif.
- `services/list_view.py`: Helper paging/filter yang dipakai halaman preview dan management.
- `services/period_analysis_workbook.py`: Generator workbook analisis periode ke Excel.
- `services/period_comparisons.py`: Orkestrasi kalkulasi analisis periodik.
- `services/period_comparison_calculators.py`: Helper kalkulasi growth (`M/M`, `Q/Q`, `Y/Y`, `YTD`, `C/C`).
- `services/upload_flow.py`: Alur unggah yang dieksekusi endpoint `/upload`.
- `docs/README_DOCS.md`: Panduan wizard dataset, migrasi `dataset_code`, changelog, taut troubleshooting.
- `services/upload_preview.py`: Penyimpanan dan pengambilan sesi preview upload.
- `services/manual_entries.py`: Helper normalisasi dan validasi input manual.

### Catatan perilaku format periode
- Marker periode diperlakukan fleksibel untuk `Triwulanan` dan `Tahunan`.
- `Triwulanan`: `YYYY-MM` dan `YYYY-Q1..YYYY-Q4` sama-sama valid.
- `Tahunan`: `YYYY` dan `YYYY-MM` valid; jika `YYYY-MM`, sistem menyimpan `month` sebagai penanda agar tampilan tetap `YYYY-MM`.
- Mekanisme ini berlaku di input manual dan unggah Excel agar perilaku konsisten.
- Skenario tambahan `Tahunan=2021` (tanpa bulan) sudah divalidasi lewat E2E untuk mode manual dan upload.

### Cakupan Fitur yang sebelumnya belum terdokumentasi
- `playwright_period_filter_smoke.spec.js` sudah tersedia sebagai smoke test untuk validasi alur filter rentang periode.
- Konsistensi komponen tombol, formulir, dan susunan tabel lintas halaman sudah distandarkan (pratinjau dan manajemen data).
- Status filter dipertahankan pada URL untuk preview dan data-management agar mudah dibagikan ulang.
- Paginasi dan reset otomatis telah diatur untuk menjaga konsistensi hasil saat halaman berubah.

## Arsitektur

### Gambaran Tingkat Tinggi
Aplikasi menerima alur unggah maupun input manual, diproses oleh parser normalisasi bersama, lalu disimpan ke `data_entries` di SQLite. Template menampilkan halaman beranda, pratinjau, manajemen data, dan dashboard; endpoint ekspor/analisis menyediakan data mentah serta hasil perhitungan pada mode analisis.

### Diagram Komponen
```
Halaman Beranda + Form
    ↓ HTTP POST
Aplikasi Flask (app.py)
    ↓ Parser / helper model
    ↓ SQLite (data_entries)
    ↓ HTTP GET
Template Preview / Data-Management / Dashboard
```

### Alur Data
1. **Aksi pengguna**: Mengunggah Excel atau mengisi formulir manual dengan metadata (`data_type`, `time_period`).
2. **Pemrosesan backend**: Validasi → parsing/normalisasi → penyimpanan ke SQLite.
3. **Respons sistem**: Menampilkan metrik terbaru, tabel terfilter, dan tautan ekspor.

### Alur Utama
1. Pengguna membuka halaman `/` untuk melihat ringkasan terkini, metadata, dan menu cepat.
2. Pengguna melakukan unggahan Excel atau input manual (keduanya memerlukan informasi penyedia data, versi, dan metadata terkait).
3. Sistem memproses data, menyimpannya, kemudian memperbarui ringkasan cache.
4. Pengguna melanjutkan analisis melalui:
   - `/preview-data` untuk meninjau data tabel dengan filter rentang periode.
   - `/data-management` untuk pemeliharaan data dan tindakan massal.
   - `/dashboard` untuk melihat metrik dan analisis periodik.
5. Semua filter terkait, termasuk `start_period`/`end_period`, ikut diterapkan pada ekspor dan analisis.

### Alur Tambahan
- `/dashboard` menampilkan metrik serta opsi analisis yang berangkat dari data aktif.
- `/export` menyediakan data mentah (CSV/Excel) sesuai filter aktif.

## Skema Basis Data

### Tabel Utama
- **data_entries**: Menyimpan metadata pengunggah, rincian waktu, `data_type`, `time_period`, indikator, dan nilai.

### Relasi
- `data_entries` adalah satu-satunya tabel data utama (tanpa cache ringkasan).

## Tumpukan Teknologi

### Frontend
- **Template engine**: Jinja2
- **Styling**: Tailwind CSS + DaisyUI (build via CLI) + CSS custom minimal
- **Distribusi aset**: Static serving dari Flask

### Backend
- **Runtime**: Python 3.12+
- **Framework**: Flask 3.1
- **Basis data**: SQLite
- **Pemrosesan Excel**: pandas + openpyxl
- **ORM/helper**: Wrapper `sqlite3` + helper internal
- **Validasi**: Fungsi validasi Python khusus + flash messaging

### DevOps & Perangkat Pendukung
- **Kontrol versi**: Git
- **Dokumentasi**: Dokumen perencanaan dan README ini
- **Pengujian sintaks**: `python -m py_compile`

### Variabel Lingkungan

File **`.env`** di root proyek (buat dari **`.env.example`**) di-load otomatis saat modul `config` pertama kali diimpor — **tidak menimpa** variabel yang sudah ada di proses (cocok untuk produksi: systemd/Docker mengisi env, file hanya untuk dev).

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Unix
```

Variabel yang dipakai aplikasi / tooling:

| Variabel | Keterangan |
|----------|------------|
| `DATABASE_URL` | DSN SQLAlchemy (wajib di produksi saat `FLASK_ENV=production`); jika kosong, fallback file SQLite `data.db` (dev). |
| `FLASK_SECRET_KEY` | Secret Flask untuk sesi; jangan pakai default di produksi. |
| `FLASK_ENV` | `production` mengaktifkan guard DSN + peringatan secret. |
| `FLASK_RUN_PORT` | Port `python app.py` (default 5000). |
| `SESSION_COOKIE_SECURE` | `1` / `true` → cookie sesi flag Secure (HTTPS). |
| `REQUIRE_FLASK_SECRET` | `1` → gagal start bila secret masih default. |
| `UPLOAD_RATE_LIMIT_MAX_REQUESTS` | Batas request upload per jendela (default 120). |
| `UPLOAD_RATE_LIMIT_WINDOW_SECONDS` | Lebar jendela detik (default 60). |
| `ALEMBIC_DATABASE_URL` | Override DSN khusus Alembic (opsional). |
| `DOTENV_PATH` | Path file env tambahan (opsional), dimuat setelah `.env`. |
| `SQLITE_SOURCE_PATH` / `MIGRATE_TARGET_URL` / `MYSQL_TARGET_URL` | Default opsional untuk skrip `scripts/migrate_sqlite_to_mysql.py`. |
| `MYSQL_SOURCE_URL` / `SQLITE_BACKUP_PATH` | Opsional untuk skrip `scripts/migrate_mysql_to_sqlite.py`. |

Contoh isi minimal lokal (bukan untuk commit):

```env
FLASK_SECRET_KEY=change-me-for-production
FLASK_RUN_PORT=5000
```

## Endpoint Aktif
```bash
GET  /                         # Beranda + ringkasan
GET,POST /upload               # Unggah file Excel
GET,POST /manual               # Input data manual
GET  /preview-data             # Pratinjau data + filter + ekspor
GET,POST /data-management      # Manajemen data + tindakan massal
GET  /dashboard               # Metrik repository + analisis periode
GET  /export                   # Ekspor CSV/Excel berdasarkan filter aktif
POST /generate-plot            # Membuat grafik garis indikator berdasarkan rentang periode
POST /generate-period-analysis  # Membuat analisis perbandingan periode
POST /export-period-analysis    # Mengekspor hasil analisis periode ke Excel
```

## Skrip yang Tersedia

Project Python dapat dijalankan dengan perintah berikut:
```bash
python app.py                  # Menjalankan server lokal
pytest                         # Menjalankan unit test
python -m py_compile app.py models.py excel_parser.py

# Aset frontend
npm run build:css
```

## Penggunaan

### Penggunaan Dasar
1. Akses `http://localhost:5000` untuk melihat ringkasan dan metadata di beranda.
2. Lakukan unggahan data melalui `/upload` atau input manual pada `/manual`.
3. Gunakan `/preview-data` untuk memfilter dan mengekspor data mentah.
4. Gunakan `/data-management` untuk pemeliharaan, pembaruan massal, serta penghapusan data.
5. Gunakan `/dashboard` untuk visualisasi dan analisis rentang periode.

### Contoh Pemakaian Endpoint
```bash
GET /preview-data?data_type=flow&time_period=monthly&start_period=2024&end_period=2024-Q4&limit=20&page=1
GET /data-management?time_period=quarterly&start_period=2024-Q1&end_period=2024-Q4
GET /export?format=csv&data_type=flow&start_period=2024&end_period=2024-Q4
GET /export?format=excel&start_period=2024&end_period=2024-Q4
POST /generate-plot (form: indicator=..., period_start=2024, period_end=2024-Q4, ...)
POST /generate-period-analysis (form: period_start=2024, end_period=2024-Q4, comparison_type=year-over-year)
POST /export-period-analysis (form: period_start=2024, end_period=2024-Q4)
```

### Cara verifikasi fitur rentang periode
1. **Preview-Data**
   - Buka `/preview-data`.
   - Isi `Rentang Periode Mulai` dan `Rentang Periode Akhir`, lalu klik `Terapkan Filter`.
   - Pastikan URL memuat `start_period` dan `end_period`, kemudian lakukan ekspor CSV/Excel dan verifikasi output mengikuti filter yang sama.
2. **Data-Management**
   - Buka `/data-management`.
   - Isi periode yang diinginkan, kirimkan filter, lalu pastikan kontrol aksi (`Hapus Berdasarkan Filter`) tersedia sesuai status filter.
3. **Dashboard**
   - Buka `/dashboard`.
   - Isi `Periode Mulai` dan `Periode Akhir` pada formulir grafik, klik `Hasilkan Grafik Garis`, lalu pastikan payload request membawa `period_start` dan `period_end`.
   - Pada **Analisis Periode**, isi rentang periode dan klik `Hasilkan Analisis Periode`; pastikan hasil dan ekspor analisis juga menggunakan rentang yang sama.

## Pedoman Pengembangan

### Gaya Kode
- Usahakan panjang baris Python tidak melebihi 120 kolom.
- Prioritaskan helper yang deskriptif (`models.py`, `excel_parser.py`, dan sebagainya).
- Dokumentasikan route/template baru sesuai kebutuhan agar mudah dipelihara.

### Alur Kerja Git
```bash
git checkout -b feature/<nama-fitur>
git add .
git commit -m "feat: ..."
git push origin feature/<nama-fitur>
```

### Strategi Pengujian
- Jalankan unit test: `pytest`.
- Jalankan `python -m py_compile ...` setelah perubahan struktural.
- Lakukan smoke test manual terhadap alur unggah/manual (lihat `QA_CHECKLIST.md`).
- Untuk skenario rentang periode, jalankan:
  - `npx playwright test simple_tests/ui_tests/playwright_period_filter_smoke.spec.js`.

## Deployment

### Kebutuhan Produksi
- Runtime Python 3.13+ (dengan Flask, pandas, openpyxl).
- Direktori kerja harus dapat menulis data ke `uploads/` dan `data.db`.
- Konfigurasi `FLASK_SECRET_KEY` untuk keamanan sesi.

### Langkah Deployment
1. Siapkan server beserta seluruh dependensi Python.
2. Pindahkan data `.db` dan folder `uploads/` (atau gunakan strategi migrasi yang disetujui tim).
3. Tetapkan variabel lingkungan (`DATABASE_URL`, `FLASK_SECRET_KEY`, dll.) lewat systemd/Docker atau salin `.env.example` → `.env` pada server bila kebijakan tim mengizinkan file env terlindungi (bukan di repo).
4. Jalankan `python app.py` melalui reverse proxy (contoh: Gunicorn + Nginx).

## Roadmap Pengembangan

### Jangka Pendek
- [ ] Menambahkan autentikasi pengguna dan jejak audit unggahan.
- [ ] Meningkatkan pengalaman error handling dan indikator loading.
- [ ] Menambah fitur ekspor PDF dan template Excel langsung.

### Jangka Menengah
- [ ] Menjadwalkan refresh agregasi secara otomatis.
- [ ] Integrasi sinkronisasi data dengan data lake.
- [ ] Menambahkan dukungan multi-bahasa untuk antarmuka.
- [ ] Menyediakan versioning API serta pembatasan request.

### Jangka Panjang
- [ ] Mengarah ke arsitektur berbasis layanan/worker queue apabila skala pertumbuhan meningkat.
- [ ] Menambahkan analitik deteksi anomali.
- [ ] Integrasi dengan dashboard BPS tingkat produksi.

## Kontribusi & Dukungan

### Cara Berkontribusi
1. Fork repositori.
2. Buat branch fitur.
3. Lakukan perubahan kode dan tambah pengujian.
4. Jalankan perintah lint/test yang diperlukan.
5. Ajukan PR untuk proses review.

### Dukungan
- Dokumentasi referensi: README ini, [`docs/README_DOCS.md`](docs/README_DOCS.md), [`docs/planning.md`](docs/planning.md), [`.cursor/plans/bps_data_management_system_bd94389d.plan.md`](.cursor/plans/bps_data_management_system_bd94389d.plan.md).
- Pertanyaan operasional: buat tiket pada GitHub Issues.

## Lisensi
MIT License.
