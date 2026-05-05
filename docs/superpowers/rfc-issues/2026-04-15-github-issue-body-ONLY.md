### Summary

Meta-issue / RFC to replace ad-hoc `sqlite3` + string SQL with **SQLAlchemy 2.0 (sync)**, keep **office production on MySQL 8**, and support **portable `DATABASE_URL`** for **SQLite** (fast dev/tests), **MySQL**, and **PostgreSQL** (CI parity). Isolate dialect differences (upsert, batch bind limits, duplicate-key detection, pooling) in small modules (“dialect quarantine”). Follow up with **Pythonic CRUD** (thin repositories, clear names, smaller functions) aligned with clean-code and light clean-architecture boundaries.

### Problem / motivation

- Persistence is tightly coupled to **SQLite-specific** SQL (`ON CONFLICT` + `excluded.*`, `datetime(created_at)` wrappers) and **sqlite3.IntegrityError** string checks in `services/upload_flow.py`.
- SQL leaks into **services** (`period_comparisons`, `upload_preview`) instead of a single persistence boundary.
- `models/__init__.py` re-exports service analytics, blurring layers.
- No versioned migrations; DDL lives in `init_db()` — risky for production office rollout.
- Hard to test against **MySQL/PostgreSQL** semantics (locking, upsert, error codes) without a deliberate plan.

**Canonical plan (checklists + tasks):**  
`docs/superpowers/plans/2026-04-15-sqlalchemy-mysql-refactor.md`  

**Related (logging + dialect transition context):**  
`docs/superpowers/plans/2026-04-13-logging-and-mysql-migration.md`

### Goals

1. **Strangler migration:** introduce Engine + scoped Session (Flask `teardown_appcontext`), keep app behavior stable for routes/templates (same public dict shapes, e.g. `tanggal_data`).
2. **Portable backends:** one codebase; `DATABASE_URL` selects dialect. Production = MySQL; dev/CI may use SQLite and/or PostgreSQL.
3. **Dialect quarantine:** `dialect_upsert.py`, `dialect_batch.py`, centralized `is_duplicate_key_error(exc, dialect_name)` (MySQL 1062, PG 23505, SQLite messages) — no scattered driver string matching in upload flows.
4. **Alembic** as source of truth for schema; avoid ad-hoc `CREATE TABLE` on startup for migrated environments.
5. **CRUD refactor (Task 13 in plan):** repository-style modules (`entries_repository` / service-level helpers), meaningful function names, reduce mega-functions in `upload_flow` / `data_management_actions`; TypedDict/dataclass at repository boundaries where it reduces ambiguity.
6. **CI:** default fast SQLite job + **integration** job(s) with MySQL service; PostgreSQL job recommended for upsert/integrity regression.

### Non-goals (for this RFC)

- Rewriting the entire UI or Excel parser semantics.
- Async SQLAlchemy / ASGI migration (remain sync unless explicitly rescoped).
- Big-bang single PR — use phased PRs mapped to plan tasks.

### Deep-module candidates (from architecture review)

| # | Cluster | Coupling | Dependency category | Test focus |
|---|---------|----------|---------------------|------------|
| 1 | `mutations` + `data_filters` + `upload_flow` | shared insert shape, upsert + duplicate semantics | behavioral / transaction | `test_upload_flow`, `test_mutations_baseline` |
| 2 | `queries` + `browse` + `pages` templates | row dict contract / `tanggal_data` | type-sharing | golden dict / contract tests on `query_data_entries` |
| 3 | `upload_preview` + mutations | duplicate probe SQL + bind limits | resource / dialect | `test_upload_preview` on real MySQL/PG in CI |
| 4 | `connection` + `init_db` + app startup | lifecycle vs migrations | lifecycle / deploy | `test_app_factory`, Alembic smoke |

### Phased delivery (mirror plan; one PR cluster per phase where possible)

| Phase | Outcome | Key paths |
|-------|---------|-----------|
| P1 | Deps + `DATABASE_URL` config + tests | `requirements.txt`, `config.py`, `tests/test_database_config.py` |
| P2 | Engine/session + Flask hooks | `infrastructure/db.py`, `app.py` |
| P3 | ORM models + Alembic initial revision | `infrastructure/orm_models.py`, `alembic/` |
| P4 | Read path strangler | `models/queries.py`, `models/browse.py` |
| P5 | Portable upsert + writes + batch chunking | `infrastructure/dialect_upsert.py`, `infrastructure/dialect_batch.py`, `models/mutations.py` |
| P6 | Browse + portable datetime columns | `models/browse.py` |
| P7 | Integrity / duplicate handling | `services/db_errors.py`, `services/upload_flow.py` |
| P8 | Move SQL out of services | `services/period_comparisons.py`, `services/upload_preview.py` |
| P9 | Decouple `models/__init__.py` re-exports | `models/__init__.py`, callers |
| P10 | CI matrix | `.github/workflows/ci.yml`, `tests/conftest.py` |
| P11 | ETL script to MySQL office | `scripts/migrate_sqlite_to_mysql.py` |
| P12 | Remove legacy sqlite3 path post-cutover | cleanup |
| P13 | Pythonic CRUD surface | `services/data_management_actions.py`, repositories |

### Acceptance criteria

- [ ] `DATABASE_URL` can point to `sqlite://`, `mysql+pymysql://`, or `postgresql+psycopg://` without changing application code outside persistence/dialect helpers.
- [ ] Engine/session options match dialect: pooled client-server for MySQL/PG; SQLite-safe pattern (`StaticPool` / `check_same_thread` per SQLAlchemy docs) for dev/tests.
- [ ] **Alembic** is authoritative for schema in migrated environments: `alembic upgrade head` on empty DB works; no reliance on ad-hoc `CREATE TABLE` / `init_db()` for prod cutover.
- [ ] Upsert behavior identical across supported DBs for the documented unique key (verified by integration tests).
- [ ] **Batch preview / duplicate probes** respect `max_batch_params(engine)` (no hard-coded SQLite 999 only in scattered code).
- [ ] Duplicate-key flows in upload/manual paths work without SQLite-specific substring checks.
- [ ] **Read-path contract:** public row dicts from list/query APIs (including computed `tanggal_data`) remain stable — covered by contract or golden tests.
- [ ] No SQLAlchemy imports under `excel_parser/`.
- [ ] **Task 13:** services call repositories / persistence API only — no raw SQL in `upload_preview` / `period_comparisons` / `data_management_actions`; TypedDict or dataclass at persistence boundary where agreed.
- [ ] Full **pytest** green on default CI; integration job(s) green on MySQL (and PostgreSQL if enabled); **Playwright** suite still green after relevant route changes.
- [ ] **ETL script** (SQLite → MySQL office): documents row-count or checksum verification step after run.
- [ ] **Post-cutover:** legacy `get_conn` / runtime DDL / sqlite3-only prod path removed or gated exclusively to dev tooling (per plan Task 12).
- [ ] **Manual smoke** documented: upload + duplicate confirm, data-management filters, period-analysis export (matches plan “Verifikasi akhir”).
- [ ] `docs/README_DOCS.md`, `docs/planning.md`, and Cursor plan stay synced when behavior-affecting PRs merge (repo rule).

### Suggested parallelization (subagents / Copilot workstreams)

Independent enough for **parallel agents** after P3 exists:

- **Agent A — Reads:** `queries` + `browse` strangler + contract tests for row dicts.
- **Agent B — Writes:** `dialect_upsert` + `mutations` + mutation/upload tests.
- **Agent C — Services:** strip SQL from `upload_preview` / `period_comparisons`; wire to repository functions.
- **Agent D — CI/infra:** workflow services, `conftest` `DATABASE_URL` fixture, README connection examples.
- **Agent E — CRUD cleanup:** Task 13 only after P4–P7 stable — `data_management_actions` + repository naming.

**Coordination:** single owner merges ordering — **P2 → P3 before parallel A/B** to avoid schema drift.

### Security / ops (office server)

- No secrets in repo; only env-based `DATABASE_URL` / pool options.
- Pool conservative on small hardware; `pool_pre_ping`, `pool_recycle` documented.
- Backup + rollback documented before production cutover (see logging/MySQL plan).
