# Dokumentasi proyek (`docs/`)

Dokumen ini jadi **indeks + ringkasan state** untuk folder `docs/`. Untuk setup cepat stack, baca [README.md](../README.md) di root repo.

---

## Baca dulu (urutan disarankan)

1. [README.md](../README.md) — instalasi, Alembic, DSN, skrip migrasi data.
2. **File ini** — peta `docs/`, unggah & dataset, rehearsal migrasi, changelog ringkas.
3. [`.cursor/plans/bps_data_management_system_bd94389d.plan.md`](../.cursor/plans/bps_data_management_system_bd94389d.plan.md) — plan Cursor (YAML todos + arsitektur), **ikut Git** (path native Cursor).
4. [troubleshooting/README.md](troubleshooting/README.md) — indeks masalah operasional (MySQL, Windows).

---

## Peta isi `docs/`

| Path | Isi |
|------|-----|
| **README_DOCS.md** (ini) | Indeks, panduan unggah/dataset, rehearsal `dataset_code`, changelog ringkas. |
| **planning.md** | Stub sinkron: README_DOCS + plan YAML di `.cursor/plans/`. |
| **plans/** | Indeks singkat; file plan ada di [`.cursor/plans/`](../.cursor/plans/). |
| **superpowers/plans/** | Rencana teknis bertahap (SQLAlchemy/MySQL, dataset-aware upload, REKAP sheet, logging). |
| **superpowers/contracts/** | Kontrak data (mis. matriks dataset). |
| **superpowers/rfc-issues/** | Ringkasan isu / RFC GitHub. |
| **troubleshooting/** | Pemecahan error produksi (1054/1050 Alembic, WinError 32 unggah). |

File **`refactor-planning.md`**, **`user_upload_datasets.md`**, dan **`migration_rehearsal_dataset_code.md`** telah digabung ke dokumen ini (2026-04-17) untuk mengurangi duplikasi.

---

## Panduan: unggah Excel & dataset

1. Buka **Unggah Data** (`/upload`).
2. Pilih **Unggah Excel** atau **Input manual**.
3. Pilih **dataset** (satu sheet REKAP = satu dataset).
4. **Unduh Template Excel** muncul setelah dataset dipilih, atau `GET /upload/template/<slug>`.
5. Baris 1 = header wajib sesuai template. Hapus contoh bila tidak dipakai.
6. Alur: unggah → **Pratinjau** → **Konfirmasi** (duplikat ditangani di UI bila ada).

**Header per dataset:** lihat [superpowers/contracts/2026-04-16-dataset-matrix.md](superpowers/contracts/2026-04-16-dataset-matrix.md) dan rencana [superpowers/plans/2026-04-16-dataset-aware-upload-manual-refactor.md](superpowers/plans/2026-04-16-dataset-aware-upload-manual-refactor.md).

**Produksi — wajib pilih dataset** (set di `.env` / systemd):

```text
REQUIRE_DATASET_FOR_UPLOAD=1
```

**Lembar Excel:** parser mencoba nama lembar: nama sheet sumber BI → strip → judul template aman → slug (file lama).

**Rollback UX:** `REQUIRE_DATASET_FOR_UPLOAD=0`. Skema DB tetap lewat Alembic; backup sebelum `upgrade head`.

---

## Migrasi & rehearsal `dataset_code`

Setelah `alembic upgrade head` (revisi `002_dataset` / `002_dataset_code_upload_runs`):

1. **Backup** dump MySQL / snapshot sebelum cut-over.
2. Baris lama memakai default `dataset_code = ''` (legacy). Unik baru: `(uploader_name, version, dataset_code, indicator_name, year, month, quarter)`.
3. **Backfill opsional** hanya jika kebijakan data setuju — contoh ilustratif (sesuaikan dialek / nama tabel):

```sql
-- UPDATE data_entries SET dataset_code = 'pinjaman' WHERE dataset_code = '' AND ...;
```

4. Verifikasi tidak ada duplikat yang melanggar unik baru (`GROUP BY` kunci + `HAVING COUNT(*) > 1`) sebelum UPDATE massal.
5. **Cut-over:** jendela maintenance; pantau log aplikasi dan `/health`.

**Operasi MySQL umum:** [troubleshooting/mysql-schema-dataset-code-and-alembic.md](troubleshooting/mysql-schema-dataset-code-and-alembic.md) + skrip `scripts/apply_dataset_code_migration.py` (`--dry-run` / `--yes`).

**Windows WinError 32** saat hapus file unggah: [troubleshooting/windows-upload-winerror-32.md](troubleshooting/windows-upload-winerror-32.md).

---

## Changelog ringkas (state fungsional)

- **2026-05-06 — Dead code removal:** Hapus `services/charts.py` (plotly visualization), `fetch_series_for_comparison` (orphan query), dead CSS selectors pivot/period-analysis, stale README route docs. Lihat issues #36, #37, #38.
- **2026-05-06 — Import cleanup:** Konsolidasi `_to_float` ke satu implementasi (`excel_parser.normalize`), hapus legacy test aliases dari `app.py`, bersihkan unused imports di `upload_flow.py` dan `repositories/__init__.py`. Issues #41–#43.
- **2026-04-17 — Dokumentasi:** `README_DOCS.md` jadi indeks utama; isi `user_upload_datasets.md`, `migration_rehearsal_dataset_code.md`, dan `refactor-planning.md` digabung ke sini lalu file itu dihapus; `planning.md` dirampingkan jadi stub sinkron; aturan Cursor di `.cursor/rules/` dilacak Git (un-ignore selektif); README root menaut ke sini.
- **2026-04-17 — Parsing periode lebih fleksibel untuk penanda:** `quarterly` dan `yearly` menerima `YYYY-MM` di input manual/upload; `2024-01` pada Triwulanan/Januari tetap tersimpan sebagai bulan marker (`year=2024`, `month=1`, `quarter=1`) agar tampilan tetap `YYYY-MM`, sementara `YYYY-Q#` tetap valid.
- **2026-04-17 — Plan Cursor di repo:** `docs/plans/bps…` lalu **2026-04-18 — `.cursor/plans/` dilacak Git:** satu file kanon `.cursor/plans/bps_data_management_system_bd94389d.plan.md` (YAML + arsitektur); `docs/plans/README.md` hanya menaut.
- **2026-04-16 — Dataset-aware:** katalog dataset, template per slug, kolom `dataset_code`, tabel `upload_runs`, parser long-format (`excel_parser/payload.py`, `dataset_long.py`), filter UI dataset-aware.
- **2026-04-16 — MySQL / Alembic:** mitigasi 1054/1050/1101/1091; migrasi idempotent `002`; skrip `apply_dataset_code_migration.py`; dokumentasi troubleshooting.
- **2026-04-16 — Windows unggah:** `pd.ExcelFile` ditutup dengan `with` agar tidak WinError 32 saat `os.remove`.
- **2026-04-16 — Agregat:** halaman ringkasan agregat dihapus; fokus data mentah + SQLAlchemy.
- **2026-04-15 — Persistensi:** SQLAlchemy multi-DB, Alembic `001_initial`, migrasi SQLite→MySQL/PostgreSQL; detail tugas di [superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md](superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md).
- **Skrip utilitas:** `scripts/flush_db.py` (hapus isi `data_entries`), `scripts/migrate_mysql_to_sqlite.py` (cadangan SQL→SQLite).

Rencana refactor struktural panjang (wave upload/period) pernah di `planning.md` / `refactor-planning.md`; narasi panjang itu **tidak** di-copy penuh ke sini — gunakan `git log -p -- docs/planning.md` atau plan SQLAlchemy di atas.

## Status plan yang belum dieksekusi (ringkas)

- **Sudah terkonfirmasi berjalan di state sekarang:** dataset-aware upload/manual, template per dataset, period marker `YYYY-MM` untuk quarterly/yearly, serta migrasi `dataset_code` + `upload_runs`.
- **Belum (utama) dari backlog docs:** `docs/superpowers/plans/2026-04-13-logging-and-mysql-migration.md` (Task 1–13 logging/audit + pipeline migrasi SQL legacy) masih largely `[ ]`.
- **Catatan:** jalur MySQL di dokumen 2026-04-13 dianggap **rujukan migrasi lama**; eksekusi kompatibilitas DB sebenarnya mengikuti `docs/superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md`.
- Untuk update eksekusi yang lebih presisi per fitur, cek `docs/README_DOCS.md` + `docs/planning.md` (stub) + `.cursor/plans/bps_data_management_system_bd94389d.plan.md`.

---

## Kontributor & agen (Cursor)

- Baca [README.md](../README.md) dan file ini sebelum mengubah perilaku atau deploy.
- Aturan Cursor yang di-commit: [.cursor/rules/planning-&-executing-sync.mdc](../.cursor/rules/planning-&-executing-sync.mdc) (sinkron docs + plan + siap produksi kantor).
- Setelah perubahan fungsional: tambahkan bullet di **Changelog ringkas**; perbarui **`.cursor/plans/bps_data_management_system_bd94389d.plan.md`** (todos YAML); perbarui `docs/planning.md` (stub) bila perlu.
