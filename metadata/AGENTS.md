## Learned User Preferences

- Prefer running Flask app directly on host rather than containerizing it inside Docker Compose, while still using Dockerized MySQL for local DB dependency.
- Prefer private repository workflow: `webdash_neraca_v2` as remote target with `main` as active sync branch.
- Prefer direct GitHub MCP-driven repo sync operations for main-branch pull/push and repository checks.
- Prefer `rtk`-prefixed command wrappers for shell execution and favor focused, low-noise command output.
- Prefer explicit alignment to `origin/main` when user says "samakan isi repo dengan main" (`git fetch` + hard sync + cleanup untracked files if requested).
- Prefer short, terse status progress updates instead of long narrative in this workspace.
- Prefer incremental `continual-learning` memory updates to process only transcript changes (new/updated by mtime), dedupe and reconcile bullets.
- Prefer removing duplicate/secondary template-download actions in upload UI and keep a single primary template download action.

## Learned Workspace Facts

- App default DB stack is SQLAlchemy with `DATABASE_URL` environment override; if unset, it falls back to local SQLite at `data.db`.
- Startup flow resolves DB URL via `database_url()`, then initializes SQLAlchemy engine and `init_db()` during app init.
- `docker-compose.mysql.yml` is configured for MySQL with `.env` credentials and named volume `webdash_mysql_data` mounted to `/var/lib/mysql` for data persistence.
- MySQL container health is checked with `mysqladmin ping`; charset and collation are set to UTF-8MB4 settings in compose command options.
- Flush/migration scripts resolve DSNs via aliases `MYSQL_TARGET_URL`, `MYSQL_SOURCE_URL`, and `MIGRATE_TARGET_URL` before defaults.
- `.env.mysql.example` provides canonical aliases for host-based Flask + Docker MySQL operations, including `DATABASE_URL`, `MYSQL_TARGET_URL`, `MYSQL_SOURCE_URL`, and `MIGRATE_TARGET_URL`.
- Pytest runs may require Python 3.11 because `requirements.txt` pins `numpy==2.3.1` (Python >=3.11).
- Upload/template workflows write files into `uploads/`; on Windows, `WinError 32` commonly indicates file lock from a still-open local Excel instance or other process, so closing those handles is required before rerunning upload/save.
