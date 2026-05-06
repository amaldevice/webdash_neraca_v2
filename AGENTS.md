## Learned User Preferences

- When quarterly (Triwulanan) period mode is selected, period fields should accept both month-style dates (e.g. `YYYY-MM`) and quarter-style labels (e.g. `YYYY-Q1`) without unnecessary parse failures.
- When debugging upload or template issues on Windows, expect questions about `PermissionError` / WinError 32 (file in use) and how that relates to apps holding file handles open.

## Learned Workspace Facts

- Default `pytest` for this repo binds a file-backed SQLite DSN before app imports so `.env` `DATABASE_URL` does not hijack the suite; use `USE_ENV_DATABASE_URL_FOR_TESTS=1` with a non-sqlite `DATABASE_URL` only when intentionally running remote-dialect integration tests.
- Installing pinned dependencies from `requirements.txt` for the full suite is reliable on Python 3.11+; Python 3.10 may fail on current pins (e.g. NumPy).
- Upload flows place working Excel copies under `uploads/`; on Windows, WinError 32 during save/delete usually means another process (often Excel preview or an open workbook) still has the file locked.
