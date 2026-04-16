# Bug & error: skema MySQL vs kode (`dataset_code`, Alembic)

Dokumen ini merangkum error yang muncul setelah deploy fitur **dataset-aware** (kolom `dataset_code`, tabel `upload_runs`, indeks unik baru) serta cara **mitigasi** dan **perbaikan**.

## Ringkasan

| Gejala | Penyebab umum | Arah perbaikan |
|--------|----------------|----------------|
| `(1054) Unknown column 'dataset_code' in 'field list'` | Aplikasi sudah revisi kode baru; DB MySQL **belum** migrasi `002_dataset`. | Jalankan migrasi Alembic hingga `002_dataset` (lihat bawah). |
| `(1050) Table 'data_entries' already exists` saat `alembic upgrade head` | Tabel dibuat manual / versi lama; tabel `alembic_version` kosong atau tidak sinkron → Alembic mengira DB kosong dan menjalankan `001_initial` dari awal. | `stamp` ke `001_initial`, lalu `upgrade head` (lihat bawah). |
| `(1101) BLOB, TEXT, … can't have a default value` pada migrasi `002` (versi lama) | MySQL melarang `DEFAULT` pada kolom `TEXT` saat `ADD COLUMN`. Revisi migrasi di repo memakai `VARCHAR(255)` + `DEFAULT ''` untuk `dataset_code`. | Tarik kode terbaru; `alembic upgrade head` lagi (atau skrip `--yes`). |
| `alembic current` masih `001_initial` padahal kolom `dataset_code` (dan seringnya `upload_runs`) sudah ada | Migrasi/setengah-patch manual; baris `alembic_version` tidak di-update ke `002_dataset`. | Verifikasi skema (kolom + tabel + indeks); jika lengkap: `python -m alembic stamp 002_dataset`. Skrip `apply_dataset_code_migration.py --yes` men-stamp otomatis bila `upload_runs` sudah ada. |
| `Duplicate entry` setelah migrasi | Data lama punya baris yang bentrok dengan kunci unik baru `(uploader, version, dataset_code, indicator, year, month, quarter)`. | Backfill / bersihkan duplikat sebelum cut-over (lihat mitigasi). |

Revisi Alembic terkait:

- `001_initial` — tabel `data_entries` + indeks unik 6 kolom (tanpa `dataset_code`).
- `002_dataset` — tambah kolom `dataset_code`, unik 7 kolom, tabel `upload_runs`.

## Mitigasi (sebelum deploy kode baru)

1. **Backup** penuh DB (dump mysqldump / snapshot VM).
2. Di **staging** dengan salinan DB: jalankan migrasi dan smoke test unggah + konfirmasi simpan.
3. Pastikan variabel lingkungan **`DATABASE_URL`** (dan bila dipakai **`ALEMBIC_DATABASE_URL`**) sama antara proses migrasi dan proses Gunicorn/Flask.
4. Jadwalkan jendela maintenance singkat untuk `upgrade` + restart app.

## Mengatasi error 1054 (`Unknown column 'dataset_code'`)

**Tujuan:** skema MySQL memuat kolom `dataset_code` dan tabel `upload_runs` seperti di `alembic/versions/002_dataset_code_upload_runs.py`.

### Langkah standar

Dari root repo, dengan DSN yang mengarah ke DB produksi/staging:

```bash
python -m alembic current
python -m alembic upgrade head
python -m alembic current
```

`current` setelah upgrade harus menunjukkan **`002_dataset`** (atau `head` sesuai penamaan chain).

### Jika skema sudah lengkap tetapi `alembic current` bukan `002_dataset`

Contoh: kolom `dataset_code` dan tabel `upload_runs` sudah ada (cek `SHOW COLUMNS` / `SHOW TABLES`), tetapi `SELECT version_num FROM alembic_version` masih `001_initial`. Tanpa sinkron ini, tim bisa salah mengira DB belum dimigrasi.

1. Pastikan indeks unik baru (7 kolom termasuk `dataset_code`) sesuai migrasi `002` — bandingkan dengan `alembic/versions/002_dataset_code_upload_runs.py`.
2. Jika yakin skema = hasil `002` penuh:

   ```bash
   python -m alembic stamp 002_dataset
   python -m alembic current
   ```

3. Atau jalankan skrip (dengan `--yes` ia men-stamp bila `upload_runs` sudah ada dan revisi masih tertinggal):

   ```bash
   python scripts/apply_dataset_code_migration.py --yes
   ```

### Jika `upgrade head` gagal dengan "Table already exists"

DB sudah punya `data_entries` tetapi Alembic tidak punya riwayat revisi `001_initial`:

```bash
python -m alembic stamp 001_initial
python -m alembic upgrade head
```

`stamp` hanya menulis baris di `alembic_version` — **tidak** mengeksekusi DDL `001`. Pastikan struktur tabel setara migrasi `001` (kolom sama dengan ORM `DataEntry` tanpa `dataset_code`).

### Skrip bantu (repo)

```bash
python scripts/apply_dataset_code_migration.py --dry-run
python scripts/apply_dataset_code_migration.py --yes
```

Skrip mendeteksi: ada/tidaknya `data_entries`, ada/tidaknya `dataset_code`, revisi Alembic saat ini; lalu menjalankan `stamp` / `upgrade` yang aman untuk kasus umum di atas.

## Setelah migrasi: verifikasi cepat (MySQL)

```sql
SHOW COLUMNS FROM data_entries LIKE 'dataset_code';
SHOW TABLES LIKE 'upload_runs';
SELECT version_num FROM alembic_version;
```

## Data & kunci unik (risiko bisnis)

- Baris lama mendapat `dataset_code` default `''` (string kosong) dari migrasi.
- Unik baru membedakan baris dengan `dataset_code` berbeda; kombinasi lama yang sama `(uploader, version, indicator, period)` dengan `dataset_code` kosong bisa **tetap satu baris** — duplikat nyata perlu dibersihkan **sebelum** atau **sesudah** migrasi sesuai kebijakan.

Lihat juga: bagian **Migrasi & rehearsal `dataset_code`** di [`docs/README_DOCS.md`](../README_DOCS.md).

## Rollback aplikasi (bukan rollback skema)

- Deploy ulang **biner aplikasi** ke versi sebelum `dataset_code` **tidak** menghapus kolom di MySQL; hanya menghindari INSERT ke kolom itu.
- Rollback **skema** (turunkan migrasi) berisiko kehilangan data di kolom baru — hindari di produksi kecuali prosedur DBA eksplisit.

## Rujukan

- `alembic/versions/002_dataset_code_upload_runs.py`
- `docs/README_DOCS.md` (alur unggah + taut ke pemecahan singkat)
- `README.md` — bagian Alembic / `DATABASE_URL`
