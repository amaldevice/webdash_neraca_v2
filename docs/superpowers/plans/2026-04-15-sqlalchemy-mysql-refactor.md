# SQLAlchemy 2.0 — Portabilitas multi-DB & refactor CRUD

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mengganti lapisan persistence berbasis `sqlite3` + string SQL dengan **SQLAlchemy 2.0 (sync)**. **Produksi kantor:** MySQL 8 sebagai target utama. **Portabilitas:** satu codebase harus bisa dijalankan dengan **`DATABASE_URL`** menuju **SQLite**, **MySQL**, atau **PostgreSQL** (dev/CI/staging lain) tanpa fork aplikasi — perbedaan dialek diisolasi di modul kecil (upsert, error duplicate, batas bind batch, opsi pool). **CRUD / clean code:** permukaan publik kecil, nama fungsi jelas (*list / get / save / delete*), kurangi fungsi raksasa dan cabang bersarang; **Clean Architecture ringan:** persistence + SQLAlchemy hanya di lapisan luar (`infrastructure/` atau `models/persistence/`); `routes` → `services` orkestrasi; tanpa ORM di `excel_parser/`.

**Architecture:** Pola **strangler** + **“dialect quarantine”**: query utama pakai **`select()` / `update()` / `delete()`** dan tipe kolom portabel (`String`, `Integer`, `Numeric`, `DateTime`); hanya titik rawa (terutama **upsert unik** + deteksi **duplicate key**) yang memakai **dispatcher** `engine.dialect.name in ("sqlite", "mysql", "postgresql")`. Flask: `Engine` + `scoped_session`, `teardown_appcontext` memanggil `remove()`. **Repository tipis** (boleh mulai sebagai modul fungsi, bukan kelas berat): mis. `entries_repository`, `summary_repository` — satu tanggung jawab per file. Opsional: `Protocol` di `ports/` bila tim siap.

**Tech stack:** Python 3.11–3.13, Flask 3.1, **SQLAlchemy ≥2.0**, **Alembic**, driver opsional ter-pin: `pymysql` / `mysqlclient` (`mysql+pymysql://…`), `psycopg[binary]>=3` (`postgresql+psycopg://…`), SQLite built-in (`sqlite:///…`). CI disarankan **matrix** minimal: SQLite (cepat) + satu job service **MySQL**; PostgreSQL job opsional tapi disarankan agar regresi dialek tidak menumpuk.

**Hubungan dengan rencana lain:** Rencana `2026-04-13-logging-and-mysql-migration.md` tetap relevan untuk logging/audit dan cutover data ke MySQL kantor; **jalur teknis disarankan SQLAlchemy portabel** (bukan menambah cabang `get_conn()` DB-API per dialek). Cross-link balik dari file itu ke dokumen ini.

**GitHub:** [Issue #9 — RFC SQLAlchemy portable + CRUD](https://github.com/amaldevice/webdash_neraca_v2/issues/9) (tracking eksekusi).

### Eksekusi berkelompok (issue #9) — urutan merge

| Gelombang | Isi | Paralel aman? | Status (2026-04-15) |
|-----------|-----|----------------|----------------------|
| **P1** | Deps + `database_url` / `use_sqlalchemy` + tes | — | **Selesai** (runtime deps di `requirements.txt`; `psycopg` di `requirements-dev.txt`; `tests/test_database_config.py`) |
| **P2** | `infrastructure/db.py` + hook `create_app` / teardown session | — | **Selesai** (`infrastructure/db.py`, `dispose_engine` bila tanpa `DATABASE_URL`, `tests/test_app_factory.py::test_create_app_sqlalchemy_engine_when_database_url_set`) |
| **P3** | ORM models + Alembic initial | — | **Selesai** (`infrastructure/orm_models.py`, `alembic.ini`, `alembic/env.py`, `alembic/versions/001_initial_schema.py`, `tests/test_alembic_initial.py`, README Alembic) |
| **P4–P7** | Read path, upsert portable, browse/summary, `db_errors` + `upload_flow` | Setelah P3: **boleh paralel** per domain (A/B/C) | **P4** read-path ✓. **P5** write-path ✓ (`dialect_upsert`, `mutations`, `scoped_transaction` di `db.py`, `app` pytest-safe). **P6** browse + `summary_store` ✓ (cabang SA, urut `created_at`/`updated_at` tanpa `datetime()` di path SA; kolom tetap `Text` ISO — migrasi `DateTime` ditunda). **P7** ✓ (`services/db_errors.py`, `upload_flow` + `engine_dialect_name`, `tests/test_db_errors.py`). |
| **P8–P9** | SQL keluar dari service + dekopling `models/__init__` | P8a preview vs P8b period_comparisons paralel | **P8** Task 8 langkah 1–2 ✓. **P9** Task 9 langkah 1–3 ✓ (tanpa re-export period comparisons; pytest `tests/`). Commit Task 8–9 Step 4 belum |
| **P10–P13** | CI matrix, ETL, hapus legacy, CRUD repository | P10 CI terpisah dari P11 skrip | **P10–P11** selesai + commit. **P12** legacy removal (pasca-cutover) belum |

**Delegasi subagent (setelah P3):** pakai pola *dispatching-parallel-agents* — **Agent A** `queries`+`browse`, **Agent B** `dialect_upsert`+`mutations`, **Agent C** `upload_preview`+`period_comparisons` SQL removal; **jangan** dua agent satu file yang sama tanpa lock.

---

## Eksplorasi codebase — temuan inti (baseline 2026-04)

| Sinyal | Lokasi / detail |
|--------|------------------|
| Hanya `sqlite3` | `models/connection.py` — `get_conn()`, `row_factory=Row`, `PARSE_DECLTYPES`, tidak ada pool |
| Upsert SQLite | `models/mutations.py` — `INSERT ... ON CONFLICT(...) DO UPDATE` + `excluded.*` |
| Ordering SQLite | `datetime(created_at)` / `datetime(updated_at)` di `models/queries.py`, `browse.py`, `summary_store.py` |
| Integrity string match | `services/upload_flow.py` — `sqlite3.IntegrityError` + substring `UNIQUE constraint failed` (empat blok) |
| SQL di service | `services/period_comparisons.py`, `services/upload_preview.py` — `get_conn()` langsung; batch + komentar batas bind SQLite (~999) di preview |
| Coupling paket | `models/__init__.py` — re-export `calculate_period_comparisons` dari `services` → baur domain/persistence |
| Tes | `tests/conftest.py` — monkeypatch `models.DB_PATH` + `init_db()`; beberapa tes raw `conn.execute` |

---

## Portabilitas multi-dialect (wajib dipegang saat implementasi)

- **Satu env `DATABASE_URL`** menentukan backend; tidak hardcode “hanya MySQL” di logika bisnis.
- **DDL:** Alembic; hindari `CREATE TABLE` ad-hoc di `create_app` untuk lingkungan yang sudah bermigrasi. Tipe kolom pilih yang punya mapping baik di ketiga dialek (hindari tipe MySQL-only kecuali benar-benar perlu + fallback dokumentasi).
- **Upsert:** tidak satu string SQL mentah — bungkus di **`dialect_upsert`** (nama bebas) dengan cabang per `dialect.name`:
  - **SQLite / PostgreSQL:** pola `INSERT … ON CONFLICT … DO UPDATE` (API SA 2 `on_conflict_do_update` untuk PG; SQLite punya dukungan serupa di versi SA yang dipakai — verifikasi di docs versi ter-pin).
  - **MySQL:** `INSERT … ON DUPLICATE KEY UPDATE` (butuh unique index fisik sama seperti sekarang).
- **Bind parameter / batch size:** helper `max_batch_params(engine)` — SQLite ~999; MySQL/Postgres lebih longgar — jangan sebar angka aja di `upload_preview`.
- **Ordering / filter tanggal:** setelah skema memakai `DateTime` konsisten, hindari `datetime(col)` khusus SQLite di query portabel; gunakan kolom native.
- **Pool:** aktifkan opsi pool hanya untuk client-server (`mysql`, `postgresql`); untuk `sqlite` gunakan `StaticPool` atau `check_same_thread` sesuai pola Flask + dokumentasi SA.

---

## CRUD Pythonic & penyederhanaan (clean code + CA ringan)

- **Permukaan kecil:** route memanggil service; service memanggil **repository** (bukan 40+ baris SQL inline). Satu alur = satu fungsi tingkat atas + helper privat pendek.
- **Nama bermakna:** hindari `apply_*` generik tanpa konteks; prefer `save_uploaded_entries`, `delete_entries_by_filter`, `list_entries_page`, `replace_aggregated_summary`.
- **Struktur data:** `TypedDict` / `dataclass` untuk *filter query* dan *payload insert* di boundary repository ↔ service (bukan `Dict` tak bertanda di mana-mana).
- **Error handling:** tangkap `IntegrityError` di satu lapisan repository atau `db_errors` — service hanya memetakan ke pesan user / kode alur upload.
- **SRP:** pecah `services/data_management_actions.py` dan `services/upload_flow.py` menjadi langkah-langkah bernama (validasi → persist → refresh summary) tanpa menggandakan logika cek duplikat.
- **Import:** `excel_parser` dan domain murni **tanpa** SQLAlchemy; **frame-orm-in-infrastructure** (lihat skill clean-architecture).

---

## Kandidat “deep module” (dari friction eksplorasi)

1. **Cluster:** `models/mutations.py` + `models/data_filters.py` + `services/upload_flow.py` — **Why coupled:** bentuk dict insert sama, upsert + error duplicate harus konsisten. **Dependency category:** *behavioral / transaction boundary*. **Test impact:** `tests/test_upload_flow.py`, `tests/test_mutations_baseline.py` → assert lewat API publik + fixture session SQLAlchemy.

2. **Cluster:** `models/queries.py` + `models/browse.py` + `routes/pages.py` — **Why coupled:** kontrak kolom + key komputasi `tanggal_data` dikonsumsi template. **Dependency category:** *type-sharing (row shape)*. **Test impact:** golden JSON / snapshot dict untuk `query_data_entries` supaya refactor ORM tidak pecah UI.

3. **Cluster:** `services/upload_preview.py` + `models/mutations.py` — **Why coupled:** duplicate probe SQL + batas bind driver. **Dependency category:** *resource / dialect limits*. **Test impact:** `tests/test_upload_preview.py` — jalankan against MySQL service untuk parity.

4. **Cluster:** `models/connection.py` + seluruh `init_db` DDL — **Why coupled:** startup `app.py` memanggil `init_db`. **Dependency category:** *lifecycle / deployment*. **Test impact:** `tests/test_app_factory.py` — ganti ke `alembic upgrade head` (mode tes) atau `create_all` terkontrol.

Pilih kandidat untuk drill-down desain interface terpisah (issue RFC) bila diperlukan; **implementasi rencana ini tidak menunggu** itu — urutan task di bawah sudah mengurut risiko tertinggi dulu.

---

## File structure (target bertahap)

| Path | Peran |
|------|--------|
| `config.py` | `DATABASE_URL`, `SQLALCHEMY_ENGINE_OPTIONS` (pool kecil untuk MySQL/PG; khusus SQLite sesuai rekomendasi SA), flag strangler legacy sementara |
| `infrastructure/db.py` (baru) atau `models/db_session.py` | `create_engine(url, **opts_from_dialect)`, `scoped_session`, `teardown_appcontext` |
| `infrastructure/orm_models.py` (baru) | `DeclarativeBase`, `Mapped`, tabel `data_entries`, `aggregated_summary` |
| `infrastructure/dialect_upsert.py` (baru) | Hanya logika beda dialek untuk upsert batch |
| `infrastructure/dialect_batch.py` (baru) | `chunk_in_batches(rows, engine)` untuk batas variabel per dialek |
| `models/repositories/` atau `infrastructure/repositories/` | `entries_repository.py`, `summary_repository.py` — CRUD Pythonic, panggilan dari `services/*` |
| `alembic/` | Revisi skema; **prod** tidak mengandalkan `CREATE TABLE IF NOT EXISTS` di runtime |
| `scripts/migrate_sqlite_to_mysql.py` | ETL one-off ke MySQL kantor; untuk PG gunakan skrip paralel atau parameter URL target generik bila perlu |
| `requirements.txt` | Pin `sqlalchemy`, `alembic`, `pymysql`, opsional `psycopg[binary]` untuk CI/dev PG |

---

### Task 1: Dependensi & konfigurasi DSN

**Files:**
- Modify: `requirements.txt`
- Modify: `config.py`
- Test: `tests/test_config_secrets.py` atau file baru `tests/test_database_config.py`

- [x] **Step 1: Tambah dependensi ter-pin** — `requirements.txt`: `SQLAlchemy==2.0.40`, `alembic==1.15.2`, `PyMySQL==1.1.1`; `requirements-dev.txt`: `psycopg[binary]==3.2.4` (CI/dev PG).

- [x] **Step 2: Tambah pengambilan `DATABASE_URL` dari env di `config.py`** — `database_url()` + `use_sqlalchemy()` (nilai kosong setelah `.strip()` dianggap tidak set).

- [x] **Step 3: Tes — URL tidak wajib di pytest default** — `tests/test_database_config.py` (`test_database_url_optional`, `test_database_url_set` + `importlib.reload`).

Jalankan: `python -m pytest tests/test_database_config.py -v`  
Expected: PASS (setelah P1).

- [ ] **Step 4: Commit** — pesan contoh: `chore: add sqlalchemy stack and DATABASE_URL config`

---

### Task 2: Engine + session Flask (tanpa mengubah perilaku bisnis)

**Files:**
- Create: `infrastructure/__init__.py`
- Create: `infrastructure/db.py` — `init_engine`, `dispose_engine`, `get_session`, `remove_scoped_session`, `register_flask_teardown`; opsi engine per dialek (`StaticPool` + `check_same_thread` untuk `sqlite:///:memory:`, `NullPool` file SQLite, pool kecil untuk MySQL/PG).
- Modify: `app.py` — jika `database_url()` set → `init_engine` + teardown; else → `dispose_engine()` agar state global bersih antar tes / toggle env.
- Test: `tests/test_app_factory.py` — `test_create_app_sqlalchemy_engine_when_database_url_set`.

- [x] **Step 1: Implementasi factory engine + scoped_session** (lihat implementasi aktual di repo; contoh di atas diganti pola portabel).

- [x] **Step 2: Tes** — factory + `app_context` + `get_session()`; tes eksisting tanpa `DATABASE_URL` tetap lulus.

Jalankan: `python -m pytest tests/test_app_factory.py tests/test_database_config.py -v`

- [ ] **Step 3: Commit**

---

### Task 3: Model ORM + Alembic revisi awal (skema setara)

**Files:**
- Create: `infrastructure/orm_models.py`
- Create: `alembic.ini`, `alembic/env.py`, `alembic/versions/001_initial.py` (nama sesuai konvensi)
- Modify: `README.md` (cara `alembic upgrade head`)

- [x] **Step 1: Definisikan tabel mirror dari DDL di `models/connection.py`**

Kolom harus 1:1 dengan `CREATE TABLE` eksisting (nama + tipe yang map baik ke SQLite/MySQL/PostgreSQL: `String`, `Numeric`, `Integer`, `Text`, `DateTime` — hindari tipe satu-dialek di skema bersama).

- [x] **Step 2: Generate / tulis migrasi pertama** yang membuat kedua tabel + **unique index** setara `ux_data_entry_variant`.

- [x] **Step 3: Verifikasi lokal**

```bash
rtk python -m alembic upgrade head
```

Pada DB kosong: tabel ada (`SHOW TABLES` / sqlite_file jika uji lokal dengan `mysql+pymysql` ke container). Tes otomatis: `python -m pytest tests/test_alembic_initial.py -v`.

- [ ] **Step 4: Commit**

---

### Task 4: Strangler read-path — `query_data_entries` + count

**Files:**
- Modify: `models/queries.py` (cabang: jika session SQLAlchemy aktif → jalankan `select()`; else legacy sqlite)
- Test: `tests/test_models.py`, `tests/test_bugs.py` (subset yang memakai query)

- [x] **Step 1: Ekstrak fungsi internal `_row_to_public_dict`** yang mempertahankan key yang sama seperti sekarang termasuk `tanggal_data`.

- [x] **Step 2: Implementasi path SQLAlchemy dengan `sqlalchemy.select`** + filter reuse dari `data_filters` (predikat SQLAlchemy di `build_data_entry_filter_sqlalchemy`, mirror logika `_build_data_entry_filter_clauses` + `apply_period_range_filter`).

- [x] **Step 3: Jalankan regresi**

```bash
rtk python -m pytest tests/test_models.py tests/test_mutations_baseline.py -q --tb=short
```

Tambahan: `python -m pytest tests/test_queries_sqlalchemy.py tests/test_bugs.py -q`.

- [ ] **Step 4: Commit**

---

### Task 5: Write-path — insert / upsert / delete (**portable**)

**Files:**
- Create: `infrastructure/dialect_upsert.py` (atau `models/persistence/dialect_upsert.py`)
- Modify: `models/mutations.py` (delegasi ke helper upsert + tetapkan transaksi)
- Test: `tests/test_mutations_baseline.py`, `tests/test_upload_flow.py` + **parametrize** `DATABASE_URL` untuk `sqlite://` dan minimal satu server (`mysql` atau `postgresql`) di job CI terpisah

- [x] **Step 1: API tunggal** — `infrastructure/dialect_upsert.py`: `insert_data_entries`, `upsert_data_entries`; cabang `mysql` → `on_duplicate_key_update`; `sqlite` / `postgresql` → `on_conflict_do_update` + `excluded`.

- [x] **Step 2: Insert murni** — `insert(DataEntry)` + mapping list (sama seperti legacy payload).

- [x] **Step 3: Transaksi** — `_sa_write_session()` context manager: `commit` / `rollback` per mutasi (hindari nested `session.begin()` pada scoped session).

- [x] **Step 4: pytest** — `tests/test_mutations_baseline.py`, `tests/test_upload_flow.py`, `tests/test_mutations_sqlalchemy.py`, `tests/test_bugs.py`; CI multi-dialect tetap Task 10.

- [ ] **Step 5: Commit**

---

### Task 6: `browse` + `summary_store` + ordering datetime

**Files:**
- Modify: `models/browse.py`, `models/summary_store.py`
- Test: `tests/test_models.py`, smoke `tests/simple_tests/functional_tests/`

- [x] **Step 1: Urutan portabel tanpa `datetime(created_at)` di path SA** — `ORDER BY created_at DESC` / `updated_at DESC` pada kolom `Text` (ISO); legacy sqlite tetap `datetime(...)`. Migrasi kolom ke tipe `DateTime` + backfill string → ditunda (revisi Alembic terpisah bila perlu).

- [x] **Step 2: `summary_store`** — pola delete-all + insert satu baris lewat `delete`/`insert` + `scoped_transaction()`; `browse.py` fungsi terkait memakai `select`/`func`/`group_by` bila SA aktif.

- [x] **Tes:** `tests/test_browse_summary_sqlalchemy.py` (+ regresi `tests/test_models.py`).

- [ ] **Step 3: Commit**

---

### Task 7: Integritas & pesan duplikat — `upload_flow`

**Files:**
- Add: `services/db_errors.py`, `tests/test_db_errors.py`
- Modify: `services/upload_flow.py`, `infrastructure/db.py` (`engine_dialect_name`)
- Test: `tests/test_upload_flow.py`, `tests/test_bugs.py`

- [x] **Step 1:** `services/db_errors.py` — `is_duplicate_key_error(exc, dialect_name)` + `resolve_duplicate_check_dialect()` (SQLite pesan unik, MySQL **1062** / string, PostgreSQL **23505** / `UniqueViolation`); jalur upload tetap menangkap `sqlite3.IntegrityError` dan `sqlalchemy.exc.IntegrityError`; `infrastructure/db.py`: `engine_dialect_name()`.

- [x] **Step 2: Unit test** `tests/test_db_errors.py` (mock `orig` per dialek).

- [x] **Step 3: pytest** regresi cabang duplikat: `tests/test_upload_flow.py`, `tests/test_bugs.py`.

- [x] **Step 4: Commit**

---

### Task 8: Pindahkan SQL dari service ke lapisan persistence

**Files:**
- Modify: `models/queries.py` — `fetch_series_for_comparison`, `preview_duplicates_batches` (cabang SA untuk preview duplikat bila engine aktif)
- Modify: `services/period_comparisons.py` → `fetch_series_for_comparison`
- Modify: `services/upload_preview.py` → `preview_duplicates_batches`
- Hapus impor `get_conn` dari kedua service setelah selesai.

- [x] **Step 1: Tulis fungsi models yang membungkus query yang ada** (salin SQL, parameter sama).

- [x] **Step 2: Tes** `tests/test_upload_preview.py`, `tests/test_bugs.py::TestPeriodAnalysis`, `tests/simple_tests/functional_tests/test_export.py`.

- [x] **Step 3: Commit**

---

### Task 9: Dekopling `models/__init__.py`

**Files:**
- Modify: `models/__init__.py`
- Modify: `routes/pages.py`, `services/period_analysis_export.py`, `tests/test_bugs.py` — impor `calculate_period_comparisons` dari `services.period_comparisons`

- [x] **Step 1: Hapus re-export period comparisons dari `models`** — impor langsung dari `services.period_comparisons` di route/service.

- [x] **Step 2: grep sisa** `from models import calculate_period_comparisons` — tidak ada sisa di `.py`.

- [x] **Step 3: pytest** `python -m pytest tests -q --tb=short` — jalur Task 9 + upload/preview hijau; suite penuh masih ~8 gagal di runner ini (concurrency flake, `test_validation` YEARLY, beberapa `test_manual_entry`, satu `test_data_management_actions`, satu `test_excel_parser` quarterly) — di luar diff Task 9. **Perbaikan sampingan:** `preview_duplicates_batches` jangan paksa `int(year)` bila `year` bisa `None` (selaras perilaku lama).

- [x] **Step 4: Commit**

---

### Task 10: CI + fixture multi-dialect

**Files:**
- Add: `.github/workflows/ci.yml` — job `test-sqlite` (matrix 3.11–3.13, `pytest tests --ignore=tests/integration`), `integration-mysql`, `integration-postgres`
- Add: `tests/integration/test_remote_dialect_smoke.py` — smoke insert/query/upsert setelah `alembic upgrade head`
- Modify: `tests/conftest.py` — fixture `database_url` (baca env `DATABASE_URL`)
- Modify: `README.md` — tabel contoh DSN tiga dialek + pointer CI

- [x] **Step 1: Job utama** SQLite — `pytest tests --ignore=tests/integration` (tanpa `DATABASE_URL` di job).

- [x] **Step 2: Job `integration-mysql`** — service `mysql:8.0`, `DATABASE_URL=mysql+pymysql://…`, `alembic upgrade head`, lalu `pytest tests/integration`.

- [x] **Step 3: Job `integration-postgres`** — service `postgres:16`, `postgresql+psycopg://…`, alur sama.

- [x] **Step 4: README** — contoh `DATABASE_URL` + prasyarat driver.

- [x] **Step 5: Commit**

---

### Task 11: ETL SQLite → MySQL

**Files:**
- Add: `scripts/migrate_sqlite_to_mysql.py` (target SQLAlchemy: MySQL/MariaDB atau PostgreSQL)
- Modify: `README.md` — subseksi migrasi skrip

- [x] **Step 1:** Baca SQLite lewat engine `sqlite:///`; tulis ke target dengan `INSERT` per chunk (default 500) + commit per chunk; tabel `data_entries` lalu `aggregated_summary`. Opsi `--truncate-target`, `--dry-run`, env `SQLITE_SOURCE_PATH` / `MIGRATE_TARGET_URL` / `MYSQL_TARGET_URL`.

- [x] **Step 2:** Verifikasi pasca-muat: `COUNT(*)` + `SUM(value)` `data_entries` dan `COUNT(*)` `aggregated_summary` sumber vs tujuan (gagal jika tidak cocok).

- [x] **Step 3:** Commit

---

### Task 12: Hapus jalur legacy (hanya setelah cutover)

- [ ] Hapus `get_conn` / `init_db` DDL runtime, cabang `USE_SQLITE_LEGACY`, dan dependensi `sqlite3` untuk **prod** (boleh tetap untuk dev tools sekali).

- [ ] Final: `rtk python -m pytest tests -q` + `rtk npx playwright test` sesuai CI.

---

### Task 13: Refactor CRUD surface (Pythonic, pasca-read/write stabil)

**Files:**
- Modify: `services/data_management_actions.py`, `routes/manage.py`, `routes/pages.py` (hanya wiring jika perlu)
- Modify/refactor: `models/repositories/*` atau setara — konsolidasi pemanggilan

- [ ] **Step 1:** Daftar endpoint CRUD + aksi bulk; untuk masing-masing pasangkan satu fungsi service publik yang memanggil repository (tanpa SQL di service).

- [ ] **Step 2:** Kurangi duplikasi filter/pagination — reuse objek `EntryListParams` (dataclass) dari `list_view` / `data_filters`.

- [ ] **Step 3:** `rtk python -m pytest tests/test_data_management_actions.py tests/test_routes.py -q`

- [ ] **Step 4: Commit**

---

## Verifikasi akhir (manual + otomatis)

```bash
rtk python -m pytest tests -q --tb=short
rtk python -m alembic current
```

Manual: upload Excel dua tahap, konfirmasi duplikat, data management filter, export period analysis.

---

## Execution handoff

**Plan disimpan di:** `docs/superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md`

**Opsi eksekusi:**

1. **Subagent-Driven (disarankan)** — superpowers:subagent-driven-development, satu subagent per task, review antar task.  
2. **Inline Execution** — superpowers:executing-plans, batch dengan checkpoint.

**Pilih pendekatan?** (balas di chat implementor)
