# Logging & Migrasi SQLite → SQLAlchemy + MySQL — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menambahkan logging terstruktur/audit pada alur CRUD, upload Excel, input manual, dan ekspor hasil analisis periode; serta **refactor persistence menyeluruh ke SQLAlchemy 2.x** dengan backend **MySQL 8** (prod / integrasi), sambil menjaga **SQLite** sebagai default dev/CI cepat sampai cutover.

**Architecture:** Tetap pola Flask (`routes` → `services` → `models`). Logging seperti sebelumnya. **Lapisan DB:** `Engine` + `sessionmaker` (atau `scoped_session`) terpusat; mapped classes / `Table` objects menggantikan string SQL + `sqlite3.Connection`. Query di `services/upload_preview.py` dan `services/period_comparisons.py` saat ini mem-bypass `models/queries.py` — naikkan ke **repository** atau fungsi `models` berbasis session agar satu dialect path. **Skema:** Alembic (disarankan) atau setara; upsert lewat dialect MySQL (`INSERT ... ON DUPLICATE KEY UPDATE`) atau `sqlalchemy.dialects.mysql.insert`.

**Tech stack:** Python 3.11–3.13 (CI), Flask 3.1, **SQLAlchemy ≥2.0**, driver **`mysqlclient` atau `pymysql`** (URL `mysql+mysqldb://` / `mysql+pymysql://`), opsional **Alembic**, pandas/openpyxl/plotly, pytest + Playwright. Dev default: SQLite via `create_engine("sqlite:///…")` + sama-sama SQLAlchemy (bukan `sqlite3` mentah) setelah refactor selesai.

---

## Konteks codebase (ringkas)

| Area | Lokasi utama |
|------|----------------|
| App factory | `app.py`, `config.py`, `wsgi.py` |
| Rute HTTP | `routes/__init__.py`, `routes/pages.py`, `routes/upload_routes.py`, `routes/manage.py` |
| CRUD & filter | `models/mutations.py`, `models/queries.py`, `models/browse.py`, `services/data_management_actions.py` |
| Upload & manual | `services/upload_flow.py`, `services/upload_preview.py`, `services/manual_entries.py`, `routes/upload_routes.py` |
| Ekspor | `routes/pages.py` (`/export`), `services/raw_export.py`, `routes/manage.py` (`/export-period-analysis`), `services/period_analysis_export.py`, `services/period_analysis_workbook.py` |
| Agregasi cache | `services/aggregation.py`, `models/summary_store.py` |
| SQL langsung di luar `models/*` | `services/upload_preview.py` (duplicate lookup batch), `services/period_comparisons.py` — target: panggil API `models` / repository |
| Pola SQLite-only (hilangkan saat SQLAlchemy) | `ON CONFLICT … DO UPDATE` + `excluded.*` di `models/mutations.py`; `ORDER BY datetime(created_at)` di `models/queries.py`, `models/browse.py`, `models/summary_store.py` |

---

## File structure (target akhir)

| File | Peran setelah pekerjaan |
|------|-------------------------|
| `config.py` | Env: logging + **`DATABASE_URL`** (sqlite / mysql), atau `USE_MYSQL` + `MYSQL_*` |
| `app.py` | Request context logging + **registrasi/teardown `Session`** (pattern: buat session per request, `remove()` di teardown) |
| `services/audit_log.py` (baru, opsional) | Helper `log_audit(event, **fields)` — satu tempat untuk field konsisten |
| `models/connection.py` | **`create_engine`**, `sessionmaker`, helper `get_session()` / inject dari app; `init_db()` → `Base.metadata.create_all` (dev) atau hanya Alembic (prod) |
| `models/db.py` atau `models/tables.py` (baru) | `DeclarativeBase`, mapped class `DataEntry`, `AggregatedSummary` (mirror kolom `init_db` sekarang) |
| `models/mutations.py`, `models/queries.py`, … | Implementasi atas **Session** + ORM / `select()`; tanpa string SQL raw kecuali fragmen terisolasi (upsert MySQL) |
| `alembic/` (baru, disarankan) | Revisi skema; versi MySQL vs SQLite bisa satu cabang env atau `env.py` baca URL |
| `services/upload_preview.py`, `services/period_comparisons.py` | Hapus `get_conn()` inline; delegasi ke `models` |
| `services/upload_flow.py`, `services/data_management_actions.py` | Audit + **`IntegrityError` dari SQLAlchemy / DBAPI** |
| `tests/` | Fixture engine SQLite in-memory + **job opsional MySQL** (service container) |

---

### Task 1: Baseline logging — konfigurasi & request correlation

**Files:**
- Modify: `config.py`
- Modify: `app.py`
- Test: `tests/test_app_factory.py` (atau file baru `tests/test_logging_request_context.py`)

- [ ] **Step 1: Tulis tes yang memverifikasi `g.request_id` ada setelah request**

```python
def test_request_id_is_set(client):
    @client.application.get("/")
    def _noop():
        from flask import g
        assert getattr(g, "request_id", None)
        return "ok"

    # Jika tidak ingin mengubah `/`, gunakan route test-only atau patch minimal:
    # Di proyek ini, cukup GET `/` lalu assert header response custom:
    pass  # Ganti: register route sementara di app test atau panggil landing_page via client.get("/")
```

Implementasi nyata: setelah `before_request` ditambahkan di `app.py`, gunakan `client.get("/")` dan asumsikan `before_request` men-set header `X-Request-ID` untuk asertai tanpa mengubah template:

```python
def test_request_id_header_on_landing(client):
    resp = client.get("/")
    assert resp.headers.get("X-Request-ID")
```

- [ ] **Step 2: Implementasi minimal di `app.py`**

```python
import uuid
from flask import g, request
from time import perf_counter

@app.before_request
def _assign_request_context():
    g.request_id = str(uuid.uuid4())
    g._t0 = perf_counter()

@app.after_request
def _add_request_id_header(response):
    rid = getattr(g, "request_id", None)
    if rid:
        response.headers["X-Request-ID"] = rid
    return response
```

- [ ] **Step 3: Konfigurasi logging root di `configure_flask_app` (`config.py`)**

```python
import logging
import os

def configure_logging(app):
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format=os.environ.get(
        "LOG_FORMAT",
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    ))
    app.logger.setLevel(level)
```

Panggil `configure_logging(app)` dari dalam `configure_flask_app` setelah `app` dibuat.

- [ ] **Step 4: Jalankan tes**

Run: `rtk pytest tests/test_app_factory.py -q` (dan file tes baru jika dibuat).

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py config.py tests/test_logging_request_context.py
git commit -m "feat(logging): request id and basic app log configuration"
```

---

### Task 2: Audit logging — data management (CRUD)

**Files:**
- Modify: `services/data_management_actions.py`
- Modify: `routes/manage.py` (opsional: log ringkas POST)
- Test: `tests/test_data_management_actions.py`

- [ ] **Step 1: Tambahkan logger modul dan log setelah `apply_data_management_post` sukses**

Di `services/data_management_actions.py` (pseudocode lokasi — sesuaikan dengan nama fungsi aktual):

```python
import logging
_log = logging.getLogger(__name__)

def apply_data_management_post(...):
    ...
    _log.info(
        "data_management_action",
        extra={
            "event": "data_management",
            "action": action,
            "request_id": getattr(g, "request_id", None),
            # tambahkan: entry_id, filter_hash, affected_count dari return value
        },
    )
```

Gunakan pola yang sama di setiap cabang `action` (`insert`, `update`, `bulk_update`, `delete_single`, `delete_by_filter`, `bulk_delete`) dengan field yang tidak memuat secret atau body penuh.

- [ ] **Step 2: Tes dengan `caplog`**

```python
import logging

def test_data_management_logs_action(client, caplog):
    caplog.set_level(logging.INFO)
    # POST ke /data-management dengan payload minimal yang sudah dipakai tes existing
    ...
    assert any("data_management_action" in r.message or "data_management" in r.message for r in caplog.records)
```

- [ ] **Step 3: `rtk pytest tests/test_data_management_actions.py -q`**

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git commit -am "feat(audit): log data management actions"
```

---

### Task 3: Audit logging — upload & konfirmasi & manual

**Files:**
- Modify: `services/upload_flow.py`
- Modify: `routes/upload_routes.py`
- Test: `tests/test_upload_flow.py`, `tests/simple_tests/functional_tests/test_manual_entry.py` (sesuaikan)

- [ ] **Step 1: Log titik-titik berikut (level INFO untuk sukses, WARNING untuk gagal)**

  - `save_uploaded_excel`: nama file aman, path relatif, ukuran byte (tanpa path sensitif produksi jika perlu redaksi).
  - `process_upload_post_file` / `process_upload_confirm`: jumlah baris yang akan dipersist, outcome (`insert` vs `upsert`), error validasi.
  - `process_manual_input_post`: duplicate vs committed, `uploader`/`version` dari form (bukan CSRF token).
  - `routes/upload_routes.py`: rate limit hit, CSRF mismatch (tanpa log nilai token).

- [ ] **Step 2: Tes**

Perluas `tests/test_upload_flow.py` dengan `caplog` untuk satu cabang sukses upload dan satu error terkontrol.

- [ ] **Step 3: `rtk pytest tests/test_upload_flow.py -q`**

- [ ] **Step 4: Commit**

---

### Task 4: Audit logging — preview session & pembersihan cache

**Files:**
- Modify: `services/upload_preview.py`
- Test: `tests/test_upload_preview.py`

- [ ] **Step 1: Log `save_preview_session`, `delete_preview_session`, eviction di `cleanup_upload_preview_cache`**

Field: `preview_token` (boleh hash 8 karakter pertama), `ttl_seconds`, alasan invalidate.

- [ ] **Step 2: `rtk pytest tests/test_upload_preview.py -q`**

- [ ] **Step 3: Commit**

---

### Task 5: Audit logging — ekspor

**Files:**
- Modify: `routes/pages.py` (`export_data`)
- Modify: `services/raw_export.py`
- Modify: `routes/manage.py` (`export_period_analysis_excel`)
- Modify: `services/period_analysis_export.py`
- Test: tambah aserti di tes export yang ada di `tests/simple_tests/functional_tests/` atau `tests/test_routes.py`

- [ ] **Step 1: Log parameter aman**

  - `/export`: `format`, jumlah baris hasil query, ringkasan filter (bukan seluruh query string jika berisi PII berlebihan).
  - `/export-period-analysis`: `indicator`, rentang tahun/periode, ukuran file response.

- [ ] **Step 2: Jalankan subset tes export**

Run: `rtk pytest tests -k export -q`

- [ ] **Step 3: Commit**

---

### Task 6: Logging di lapisan mutasi DB (opsional tapi direkomendasikan)

**Files:**
- Modify: `models/mutations.py`
- Test: `tests/test_mutations_baseline.py`

- [ ] **Step 1: Setelah `_execute_mutation` sukses, log INFO dengan `operation` dan `rowcount`**

Hindari duplikasi berlebihan jika Task 2–4 sudah log detail bisnis; gunakan ini sebagai **jejak DB** tipis:

```python
_log.info("db_mutation_ok", extra={"operation": operation, "rowcount": cursor.rowcount if cursor else None})
```

- [ ] **Step 2: `rtk pytest tests/test_mutations_baseline.py -q`**

- [ ] **Step 3: Commit**

---

### Task 7: Agregasi / summary store

**Files:**
- Modify: `services/aggregation.py`
- Modify: `models/summary_store.py`

- [ ] **Step 1: Log awal/akhir `refresh_aggregated_summary` dengan durasi dan ukuran JSON (bytes atau len keys)**

- [ ] **Step 2: `rtk pytest tests -k aggregation -q`** (sesuaikan pola `-k`)

- [ ] **Step 3: Commit**

---

## Bagian B: Refactor SQLAlchemy + cutover MySQL

Urutan disarankan: **inventory → engine/session + deps → mapped schema + migrasi skema → port `models/*` → tarik query dari `services/*` → error helper + upload → skrip data + CI MySQL → pool/health.**

### Task 8: Inventarisasi titik sentuh DB — dokumen internal

**Files:**
- Create: `docs/superpowers/notes/sqlalchemy-mysql-migration-inventory.md` (disarankan; bisa menggabungkan catatan MySQL lama)
- Modify: None

- [ ] **Step 1: Grep jejak persistence**

Run:

```bash
rtk rg "sqlite3|get_conn\\(|ON CONFLICT|datetime\\(|IntegrityError|\\.execute\\(" models services routes tests
```

Pastikan entri untuk: `models/{connection,mutations,queries,browse,summary_store,data_filters}.py`, `services/upload_flow.py`, `services/upload_preview.py`, `services/period_comparisons.py`, pemanggilan `get_conn` di `tests/`.

- [ ] **Step 2: Tabel per-file — “input saat ini” vs “target SQLAlchemy”**

Contoh baris wajib:

| File | Saat ini | Target |
|------|----------|--------|
| `models/connection.py` | `sqlite3.connect` + `init_db()` DDL string | `create_engine` + `sessionmaker`, `init_db` → `metadata.create_all` (dev) |
| `models/mutations.py` | `ON CONFLICT … DO UPDATE`, `?` binds | `session.add_all` / `merge` / `mysql.insert().on_duplicate_key_update` |
| `models/queries.py` | `sqlite3.Row`, `datetime(created_at)` | `select()` + `order_by(DataEntry.created_at.desc())`; tipe kolom datetime konsisten |
| `models/browse.py`, `summary_store.py` | `datetime(...)` di ORDER BY | sama; hasil mapping ke `dict` seperti sekarang |
| `services/upload_preview.py` | SQL batch OR | fungsi di `models` + `or_` / `tuple_in` batched |
| `services/period_comparisons.py` | SELECT manual | `models` query function + session |

- [ ] **Step 3: Commit dokumen**

---

### Task 9: Dependensi + `Engine` / `Session` (default SQLite tidak regresi)

**Files:**
- Modify: `requirements.txt` — `SQLAlchemy>=2.0`, driver MySQL (`pymysql` atau `mysqlclient`), opsional `alembic`
- Modify: `config.py` — baca `DATABASE_URL`; fallback `sqlite:///${BASE_DIR}/data.db` (URL, bukan path mentah) atau env eksplisit
- Modify: `models/connection.py` — `engine`, `SessionLocal`, `get_session()` context manager; **deprecate** `get_conn()` setelah port (atau shim tipis sementara hanya untuk tes transisional)
- Modify: `app.py` — `scoped_session` atau session per-request + `teardown_appcontext` → `session.remove()`
- Test: `tests/conftest.py` — fixture `db_session` / override `DATABASE_URL` ke SQLite `:memory:`

- [ ] **Step 1: Pin versi & instal lokal**

- [ ] **Step 2: Satu tes smoke: `init_db` + insert satu baris lewat ORM** (file baru ringkas atau perluas `tests/test_models.py`)

- [ ] **Step 3: `rtk pytest tests/test_models.py tests/test_app_factory.py -q`**

- [ ] **Step 4: Commit**

---

### Task 10: Mapped tables + Alembic (skema MySQL = sumber kebenaran prod)

**Files:**
- Create: `models/tables.py` atau `models/orm.py` — `DeclarativeBase`, `DataEntry`, `AggregatedSummary` (kolom selaras `init_db` + index unik `ux_data_entry_variant`)
- Create: `alembic.ini`, `alembic/env.py`, revisi awal `001_initial.py`
- Modify: `models/connection.py` — impor metadata dari ORM

- [ ] **Step 1: Revisi awal menghasilkan DDL MySQL 8** (`BIGINT` PK, `DATETIME(6)` untuk `created_at` / `updated_at`, `TEXT`/`VARCHAR` selebihnya selaras kebutuhan query)

- [ ] **Step 2: SQLite dev** — `create_all` dari metadata yang sama (hindari fitur MySQL-only di mapped column kecuali pakai `TypeDecorator` / cabang)

- [ ] **Step 3: Dokumentasikan `alembic upgrade head` untuk deploy**

- [ ] **Step 4: Commit**

---

### Task 11: Port lapisan `models/*` dari raw SQL → Session/ORM

**Files:**
- Modify: `models/mutations.py`, `models/queries.py`, `models/browse.py`, `models/summary_store.py`, `models/data_filters.py` (bantu `filter` dengan `column.op` / `func.lower`)

- [ ] **Step 1: Mutations** — insert bulk, upsert (MySQL: `on_duplicate_key_update`; SQLite dev: `session.merge` per baris atau `insert().on_conflict_do_update` dialect SQLite), delete/update/bulk sama perilaku + `rowcount`

- [ ] **Step 2: Queries/browse/summary** — ganti `sqlite3.Row` dengan objek ORM atau `Row` SQLAlchemy; hilangkan `datetime()` SQL — gunakan kolom bertipe `DateTime` atau `func` portabel

- [ ] **Step 3: `rtk pytest tests -q` pada SQLite**

- [ ] **Step 4: Commit**

---

### Task 12: Konsolidasi SQL di `services/*` ke `models`

**Files:**
- Modify: `services/upload_preview.py` — panggil `models` (mis. `find_entries_by_indicator_period_batch(keys)`)
- Modify: `services/period_comparisons.py` — panggil `models` (mis. `load_indicator_series_for_comparisons(...)`)
- Create (opsional): `models/repositories/data_entries.py` jika `mutations.py` membengkak

- [ ] **Step 1: Pastikan tidak ada `from models import get_conn` di `services/` kecuali sementara shim**

- [ ] **Step 2: Tes terkait upload preview & period comparison**

- [ ] **Step 3: Commit**

---

### Task 13: `db_errors` + `upload_flow` (Integrity / rollback)

**Files:**
- Create: `models/db_errors.py` — `is_unique_violation(exc)`, opsional `is_operational(exc)` menggantikan `sqlite3.OperationalError`
- Modify: `services/upload_flow.py` — tangkap `sqlalchemy.exc.IntegrityError` (bungkus DBAPI lama)

- [ ] **Step 1: Unit test helper dengan raise palsu dari SQLite & MySQL driver**

- [ ] **Step 2: `rtk pytest tests/test_upload_flow.py tests/test_bugs.py -q`**

- [ ] **Step 3: Commit**

---

### Task 14: Migrasi data SQLite (`data.db`) → MySQL

**Files:**
- Create: `scripts/migrate_sqlite_to_mysql.py` — baca URL sqlite lama, tulis via SQLAlchemy ke engine MySQL (chunked `session.add_all` / bulk insert)
- Modify: `README.md` — env `DATABASE_URL`, urutan cutover, backup

- [ ] **Step 1: Verifikasi count baris + checksum sample per tabel**

- [ ] **Step 2: Opsional:** pertahankan `scripts/schema_mysql.sql` sebagai artefak review DBA (bukan sumber utama jika Alembic dipakai)

- [ ] **Step 3: Commit**

---

### Task 15: CI MySQL + pool + health

**Files:**
- Modify: workflow CI (jika ada) — service `mysql:8`, env `DATABASE_URL=mysql+pymysql://…`, subset tes integrasi
- Modify: `models/connection.py` — `pool_pre_ping=True`, `pool_size` / `max_overflow`, timeout dokumentasi
- Modify: `routes/` atau `app.py` — `/healthz` dengan `select(1)` via session

- [ ] **Step 1: Job opsional tidak memblokir default PR bila MySQL tidak tersedia**

- [ ] **Step 2: Commit**

---

## Self-review (ceklist penulis rencana)

| Requirement asli | Task yang menutup |
|------------------|-------------------|
| Logging CRUD | Task 2, 6 |
| Logging upload | Task 3, 4 |
| Logging manual | Task 3 |
| Logging export periode & raw | Task 5 |
| Best practices (correlation, no secrets, levels) | Task 1, catatan di Task 2–5 |
| Refactor SQLAlchemy + cutover MySQL | Task 8–15 |
| Lokasi ubahan terperinci | Tabel konteks + per-task file lists |

**Placeholder scan:** Tidak menggunakan TBD pada langkah wajib; langkah `pass` pada Task 1 harus diganti implementasi konkret sesuai pola tes proyek.

---

## Execution handoff

**Plan disimpan di:** `docs/superpowers/plans/2026-04-13-logging-and-mysql-migration.md`

**Catatan perintah deprecated:** Gunakan pola **superpowers writing-plans** (dokumen ini) alih-alih perintah `/write-plan` yang akan dihapus.

**Dua opsi eksekusi:**

1. **Subagent-driven (disarankan)** — subagent per task cluster dengan review di antara task; gunakan skill **superpowers:subagent-driven-development**.
2. **Inline execution** — eksekusi berurutan di sesi ini dengan checkpoint; gunakan skill **superpowers:executing-plans**.

**Brainstorming / spesifikasi terpisah:** Jika Anda ingin gate persetujuan formal sebelum kode (skill brainstorming), kita bisa mengekstrak Bagian A & B menjadi `docs/superpowers/specs/2026-04-13-logging-mysql-design.md` dan commit terpisah; rencana ini sudah cukup untuk memulai implementasi bertahap.

**Sinkronisasi `planning.md`:** Lakukan saat PR implementasi menyentuh perilaku; aturan workspace mengharuskan update `planning.md` dan `c:\Users\PENGOLAHAN\.cursor\plans\bps_data_management_system_bd94389d.plan.md` bersamaan dengan perubahan fungsional.

---

## Verifikasi akhir (setelah seluruh checkbox selesai)

```bash
rtk pytest tests -q
rtk npx playwright test
```

Manual: unggah file contoh, konfirmasi duplikat, input manual satu baris, ekspor CSV/XLSX, ekspor period analysis, cek log stdout untuk `request_id` dan event audit.
