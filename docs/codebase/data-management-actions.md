# Data management POST actions — transactional model (campuran)

Decisi triage **GitHub #83** (`ready-for-agent`): model **campuran** — tidak memaksa satu transaksi besar untuk seluruh permukaan `/data-management`, tetapi mutasi individual di lapisan model memakai `write_session` / commit yang jelas di mana sudah diperlukan.

## Lapisan publik

- **`services/data_management_actions.apply_data_management_post`** — satu POST form → satu **aksi** (`delete_single`, `bulk_delete`, `update`, …). Handler Flask memanggil ini lalu `flash()` untuk setiap tuple pesan.
- **`routes/manage.py`** — setelah POST sukses, redirect ke `data_management` dengan query dari **`EntryListParams.to_data_management_redirect_query()`** (kunci periode `start_period` / `end_period`, bukan `period_start` / `period_end`).

## Di mana transaksi?

- **`models/mutations.py`** — fungsi penulisan memakai **`infrastructure.db.write_session`** (atau pola setara) agar commit/rollback per operasi konsisten pada engine SQLAlchemy.
- **`apply_data_management_post`** sendiri **tidak** membungkus semua cabang dalam satu `with write_session` global; aksi yang berbeda tetap independen. Bila nanti ada aksi multi-langkah yang harus atomik, bungkus **hanya** cabang itu dengan satu `write_session` / satu transaksi eksplisit — jangan menggandakan logika flush di banyak tempat.

## Rujukan terkait

- Urutan audit unggah vs baris data: [upload-audit-transactions.md](upload-audit-transactions.md).
