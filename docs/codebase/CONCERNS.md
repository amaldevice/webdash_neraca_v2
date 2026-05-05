# Isu, Risiko, dan Dead Code Kandidat

## Isu Teknis yang Perlu Diperhatikan

1. **No CI Terdeteksi**
   - Tidak ada pipeline otomatis terpasang menurut scan.
   - Dampak: regresi testing bisa terlambat terdeteksi.

2. **Dokumentasi dan Kode Tidak Selalu Sinkron**
   - Beberapa dokumen lama masih menyebut fitur agregasi yang sudah dinonaktifkan.
   - `docs/README_DOCS.md` dan `README.md` harus menjadi sumber utama setelah refactor.

3. **Security & Reliability**
   - Terdapat dokumentasi bug hunting yang mencatat isu kritikal; perlu verifikasi ulang apakah sudah tertutup di versi saat ini.
   - Beberapa modul legacy di docs/AGENTS dan changelog menunjukkan fase transisi dari `models.py` monolit.

4. **Template Generator & Repo Hygiene**
   - Folder `docs/codebase` awalnya tidak punya template dokumen yang diharapkan oleh workflow tertentu; kini file struktur dibuat manual.
   - Pastikan workflow docs tidak bergantung pada path template eksternal yang tidak ada.

5. **Dead path untuk operasi ops**
   - Script migrasi/flush aktif, tetapi tidak dipanggil oleh app runtime.
   - Keputusan pemangkasan harus mempertimbangkan kebutuhan operasi manual (maintenance/ops).

## Dead Code/Kode yang Tidak Dipakai pada Web App Runtime

Kandidat **aman secara fungsional untuk dipilih** setelah konfirmasi kebutuhan ops:

- `scripts/build_rekap_long_templates.py`  
  - CLI satu-shot untuk regenerate template long format; tidak diimpor runtime web.
- `scripts/flush_db.py`  
  - Utility pengosongan tabel `data_entries` untuk ops/maintenance; tidak route-registered.
- `scripts/migrate_sqlite_to_mysql.py`  
  - ETL migrasi satu arah ke SQLAlchemy target; dipakai saat migrasi data, bukan request path web.
- `scripts/migrate_mysql_to_sqlite.py`  
  - ETL backup/copy terbalik; tidak dipakai oleh endpoint Flask.

### Rekomendasi

- Jika tim ingin menyederhanakan repo untuk webapp-only:
  - pindahkan ke folder `ops-tools/` atau `scripts/legacy/`,
  - atau arsipkan ke repo terpisah,
  - perbarui docs yang mereferensikan skrip tersebut.
- Jangan hapus langsung saat dokumentasi runbook (`README.md`, `SERVER_DEPLOYMENT.md`, `docs/README_DOCS.md`) masih mengacu padanya.

## Hidden Facts yang Penting

- App factory menolak startup production jika `FLASK_ENV=production` tanpa `DATABASE_URL`.
- Preview upload disimpan di disk untuk menjaga state saat multi-worker.
- Duplicate warning dan overwrite actual tidak sama: warning memakai indikator+periode, tapi persist mengikuti unique key DB.
- Parsing periode untuk `quarterly`/`yearly` mendukung marker `YYYY-MM` dengan `month` sebagai penanda visual.
- `dataset_code` masuk ke unique key untuk menghindari tabrakan antar dataset.

