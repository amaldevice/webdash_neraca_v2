# Panduan singkat: unggah & dataset (Fase 6)

## Alur wizard

1. Buka **Unggah Data** (`/upload`).
2. Pilih mode **Unggah Excel** atau **Input manual**.
3. Pilih **dataset / tabel** (satu sheet REKAP = satu dataset).
4. Unduh **template long-format** per dataset (tombol setelah dataset dipilih, atau `GET /upload/template/<slug>`).
5. Isi baris data (baris 1 = header wajib). Hapus contoh bila tidak dipakai.
6. Unggah → **Pratinjau** → **Konfirmasi** bila tidak ada duplikat, atau atasi duplikat di UI.

## Kolom wajib per dataset

Header persis seperti template (huruf kecil, underscore). Rincian per sheet ada di:

- `docs/superpowers/contracts/2026-04-16-dataset-matrix.md`
- `docs/superpowers/plans/2026-04-16-dataset-aware-upload-manual-refactor.md`

## Mode produksi: wajib pilih dataset

Set di lingkungan (systemd / `.env`):

```text
REQUIRE_DATASET_FOR_UPLOAD=1
```

Dengan nilai truthy, form menolak unggah/manual tanpa `dataset_slug` — mengurangi data masuk format generik yang tidak ter-audit per dataset.

## Lembar Excel

Parser mencoba nama lembar dalam urutan: nama sheet sumber BI persis → versi strip → judul template aman → slug (file lama). Template yang dihasilkan aplikasi memakai judul selaras sheet sumber (mis. `ATM`, `Kartu kredit`).

## Rollback

- Nonaktifkan kembali gate: `REQUIRE_DATASET_FOR_UPLOAD=0`.
- Skema DB: tetap gunakan migrasi Alembic; backup sebelum `upgrade head` di server kantor.
