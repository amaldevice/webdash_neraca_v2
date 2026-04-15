# Logging & Migrasi SQLite → MySQL — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menambahkan logging terstruktur/audit pada alur CRUD, upload Excel, input manual, dan ekspor hasil analisis periode; serta merencanakan migrasi persistence dari SQLite ke MySQL dengan risiko SQL dialect dan koneksi yang terkendali. **Selaras portabilitas:** implementasi jangka panjang mengikuti **`2026-04-15-sqlalchemy-mysql-refactor.md`** — backend bisa **SQLite / MySQL / PostgreSQL** lewat `DATABASE_URL` (kantor tetap MySQL); **CRUD** diarahkan ke permukaan repository Pythonic (kurang kompleks, mudah diuji).

**Architecture:** Tetap mempertahankan pola Flask saat ini (`routes` → `services` → `models`). Logging dikonfigurasi sekali di bootstrap aplikasi (`create_app` / `configure_flask_app`), correlation id per request via `g`, pesan audit di boundary layanan (`services/*`) dan opsional wrap terpusat di `models/mutations.py`. Migrasi MySQL memfokuskan perubahan pada `models/connection.py`, semua SQL di `models/*.py`, serta penyesuaian exception handling (`sqlite3.IntegrityError` → driver MySQL) di `services/upload_flow.py` dan modul terkait — **setelah SQLAlchemy:** exception + upsert dibungkus modul portabel (bukan string error per DB tersebar).

**SQLAlchemy (disarankan untuk integrasi penuh):** Rencana langkah demi langkah untuk ORM/session, Alembic, strangler read/write, **dialek multi-DB** (quarantine upsert/integrity/batch), CI matrix, dan **Task 13 refactor CRUD** ada di **`docs/superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md`**. **Tracking isu:** https://github.com/amaldevice/webdash_neraca_v2/issues/9. Task MySQL mentah (DB-API kompatibel dengan `get_conn`) di dokumen ini tetap berguna sebagai konteks risiko dialect untuk transisi; hindari membangun dua lapisan abstraksi paralel — pilih SQLAlchemy portabel sebagai sumber kebenaran.

**Tech stack:** Python 3.11–3.13 (CI), Flask 3.1, `sqlite3` + DDL di `models/connection.py`, pandas/openpyxl/plotly, pytest + Playwright.

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
| SQL khusus SQLite (baseline) | `ON CONFLICT ... DO UPDATE` + `excluded.*` di `models/mutations.py`; `datetime(created_at)` di query/browse/summary — diganti pola portabel di rencana 2026-04-15 |

---

## File structure (target akhir)

| File | Peran setelah pekerjaan |
|------|-------------------------|
| `config.py` | Env untuk `LOG_LEVEL`, `LOG_FORMAT` (text/json), opsional `DATABASE_URL` / `MYSQL_*` |
| `app.py` | `before_request` / `after_request` atau `teardown_request` untuk `g.request_id`, durasi, status |
| `services/audit_log.py` (baru, opsional) | Helper `log_audit(event, **fields)` — satu tempat untuk field konsisten |
| `models/connection.py` | Factory koneksi DB (tetap API `get_conn()` atau pengganti bertipe protocol) |
| `models/mutations.py` | Delegasi ke repository + `dialect_upsert` portabel; logging operasi sukses + rowcount |
| `services/upload_flow.py`, `services/data_management_actions.py` | Audit outcome upload/manual/CRUD |
| `tests/` | Fixture DB MySQL opsional; tes logging dengan `caplog` |

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

## Bagian B: Migrasi SQLite → MySQL

### Task 8: Inventarisasi SQL & tipe — dokumen internal

**Files:**
- Create: `docs/superpowers/notes/mysql-migration-sql-inventory.md` (atau seksi di rencana ini saja)
- Modify: None

- [ ] **Step 1: Grep semua `sqlite3`, `ON CONFLICT`, `datetime(`, `?` placeholder, `INSERT OR`**

Run:

```bash
rtk rg "sqlite3|ON CONFLICT|datetime\\(|IntegrityError" models services routes
```

- [ ] **Step 2: Tabel hasil untuk setiap file `models/*.py` — statement yang perlu rewrite**

Output harus mencakup minimal: `models/mutations.py` (upsert), `models/queries.py`, `models/browse.py`, `models/summary_store.py`.

- [ ] **Step 3: Commit dokumen**

---

### Task 9: Konfigurasi & koneksi MySQL (tanpa mengubah perilaku default dev)

**Files:**
- Modify: `config.py`
- Modify: `models/connection.py`
- Modify: `requirements.txt`
- Test: `tests/conftest.py` (tetap pakai SQLite default)

- [ ] **Step 1: Tambahkan dependensi driver**

Contoh (pilih satu strategi resmi tim):

```
mysqlclient>=2.2.0
```

atau

```
pymysql>=1.1.0
```

- [ ] **Step 2: Variabel lingkungan**

`DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname` atau `USE_MYSQL=1` + `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.

- [ ] **Step 3: Implementasi `get_conn()` bertingkat**

Pola aman: jika `USE_MYSQL` falsy, pertahankan perilaku SQLite sekarang; jika true, return koneksi MySQL dengan API yang kompatibel (`cursor()`, `commit()`, `rowcount`). **Catatan:** `sqlite3.Row` tidak ada di DB-API MySQL mentah — pertimbangkan wrapper kecil `dict_row(cursor)` atau gunakan SQLAlchemy core untuk hasil konsisten (tambah scope jika dipilih).

- [ ] **Step 4: Tes CI**

Tambahkan job opsional GitHub Actions dengan service `mysql:8` hanya untuk integrasi terbatas (lihat Task 12).

- [ ] **Step 5: Commit**

---

### Task 10: Skema MySQL & skrip migrasi data

**Files:**
- Create: `scripts/migrate_sqlite_to_mysql.py` (one-off)
- Create: `scripts/schema_mysql.sql` (DDL setara)

- [ ] **Step 1: DDL MySQL setara dengan `init_db()`**

Mapping contoh:

- `INTEGER PRIMARY KEY AUTOINCREMENT` → `BIGINT PRIMARY KEY AUTO_INCREMENT`
- `TEXT` → `VARCHAR(255)` atau `TEXT` tergantung kolom; `created_at`/`updated_at` idealnya `DATETIME(6)` + migrasi data dari ISO string.
- Unique index `ux_data_entry_variant` tetap sama.

- [ ] **Step 2: Skrip salin data**

Baca dari SQLite `data_entries` dan `aggregated_summary`, tulis ke MySQL dalam batch (gunakan `pandas.read_sql` + `to_sql` hanya jika tim setuju; sebaliknya `INSERT` berparameter dalam chunk).

- [ ] **Step 3: Dokumentasikan urutan cutover** (maintenance window, backup `data.db`, verifikasi counts).

- [ ] **Step 4: Commit**

---

### Task 11: Rewrite upsert & fungsi datetime di query

**Files:**
- Modify: `models/mutations.py`
- Modify: `models/queries.py`
- Modify: `models/browse.py`
- Modify: `models/summary_store.py`

- [ ] **Step 1: Ganti `ON CONFLICT ... DO UPDATE` dengan `INSERT ... ON DUPLICATE KEY UPDATE`**

Pastikan daftar kolom update mencerminkan kolom yang sekarang di-update dari `excluded.*`.

- [ ] **Step 2: Ganti `ORDER BY datetime(created_at)` dengan `ORDER BY created_at` setelah kolom bertipe datetime**

Jika skema masih TEXT sementara: gunakan `STR_TO_DATE(created_at, '%Y-%m-%dT%H:%i:%s')` atau setara untuk ISO yang dipakai aplikasi (`utc_now_iso`).

- [ ] **Step 3: Tes pytest penuh pada SQLite** memastikan tidak ada regresi sebelum flip env.

Run: `rtk pytest tests -q`

- [ ] **Step 4: Tes pada MySQL** (lihat Task 12).

- [ ] **Step 5: Commit**

---

### Task 12: Exception mapping & layanan yang menyentuh DB langsung

**Files:**
- Modify: `services/upload_flow.py` (tangkap integrity error generik / pymysql `IntegrityError`)
- Modify: `services/upload_preview.py` (batch size / limit bind)
- Modify: `services/period_comparisons.py` jika query spesifik SQLite

- [ ] **Step 1: Modul `models/db_errors.py` (baru) dengan `is_unique_violation(exc: BaseException) -> bool`**

Implementasi cabang untuk `sqlite3.IntegrityError` dan driver MySQL.

- [ ] **Step 2: Ganti pengecekan `sqlite3.IntegrityError` tersebar dengan helper**

- [ ] **Step 3: Integrasi tes**

Gunakan container MySQL lokal atau job CI: `pytest tests/test_upload_flow.py tests/test_models.py -q` dengan env `USE_MYSQL=1`.

- [ ] **Step 4: Commit**

---

### Task 13: Pooling, healthcheck, operasi

**Files:**
- Modify: `models/connection.py` atau modul pool baru
- Modify: `README.md` (deployment)

- [ ] **Step 1: Dokumentasikan ukuran pool, `connect_timeout`, `read_timeout`**

- [ ] **Step 2: Endpoint health opsional `/healthz` yang menjalankan `SELECT 1`**

- [ ] **Step 3: Commit**

---

## Self-review (ceklist penulis rencana)

| Requirement asli | Task yang menutup |
|------------------|-------------------|
| Logging CRUD | Task 2, 6 |
| Logging upload | Task 3, 4 |
| Logging manual | Task 3 |
| Logging export periode & raw | Task 5 |
| Best practices (correlation, no secrets, levels) | Task 1, catatan di Task 2–5 |
| Migrasi SQLite → MySQL | Task 8–13 |
| Lokasi ubahan terperinci | Tabel konteks + per-task file lists |

**Placeholder scan:** Tidak menggunakan TBD pada langkah wajib; langkah `pass` pada Task 1 harus diganti implementasi konkret sesuai pola tes proyek.

---

## Execution handoff

**Plan disimpan di:** `docs/superpowers/plans/2026-04-13-logging-and-mysql-migration.md`

**Rencana induk SQLAlchemy + MySQL:** `docs/superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md`

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
