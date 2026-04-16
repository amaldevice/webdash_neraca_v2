# Rehearsal migrasi `dataset_code` (Fase 5)

Setelah `alembic upgrade head` (revisi `002_dataset_code_upload_runs`):

1. **Backup** file DB / dump MySQL sebelum cut-over.
2. Baris lama memakai default `dataset_code = ''` (legacy). Unik baru: `(uploader_name, version, dataset_code, indicator_name, year, month, quarter)`.
3. **Backfill opsional** (heuristik hanya jika kebijakan data setuju), contoh ilustratif SQLite — sesuaikan nama tabel/dialek:

```sql
-- Contoh: menandai subset baris (sesuaikan WHERE dengan aturan bisnis Anda)
-- UPDATE data_entries SET dataset_code = 'pinjaman' WHERE dataset_code = '' AND ...;
```

4. Verifikasi tidak ada duplikat yang melanggar unik baru sebelum menjalankan UPDATE massal (query agregasi `GROUP BY` kunci unik + `HAVING COUNT(*) > 1`).
5. **Cut-over produksi**: jalankan migrasi di jendela maintenance; pantau log aplikasi dan `/health`.
