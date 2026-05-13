# Testing strategy & commands

## Canonical smoke (Python)

From **repository root**:

```bash
python -m pytest tests --ignore=tests/integration -q
```

(`rtk python -m pytest …` when RTK wrapper available.) This is the default regression slice: unit + route + upload flow tests under `tests/`, excluding long-running **integration** tests that need a real non-SQLite DSN.

## Default `DATABASE_URL` vs integration

- **`tests/conftest.py`** sets `DATABASE_URL` to an in-repo SQLite file **before** `models` import (unless opted out), so a developer `.env` pointing at MySQL/PostgreSQL does not hijack the default suite.
- **Remote dialect / integration:** set `USE_ENV_DATABASE_URL_FOR_TESTS` to `1`, `true`, `yes`, or `on`, **and** set `DATABASE_URL` to a non-sqlite DSN. Then run only the integration subset you need, for example:

  ```bash
  USE_ENV_DATABASE_URL_FOR_TESTS=1 DATABASE_URL=mysql+pymysql://... python -m pytest tests/integration/test_remote_dialect_smoke.py -q
  ```

  Target database must already have schema from `alembic upgrade head`.

## Subprocess / config tests (`WEBDASH_SKIP_DOTENV`)

`tests/test_config_secrets.py` runs a **subprocess** without `pytest` in `sys.modules` to assert production secret warnings. It sets **`WEBDASH_SKIP_DOTENV=1`** so `load_dotenv` does not override env from a local `.env` during that scenario. Use the same flag in any ad-hoc script that must mirror that behaviour.

## CI / workflows

GitHub Actions (or other CI) configuration lives under `.github/workflows/` when present. This document does **not** guarantee job names or matrix versions stay in sync with local pins—after changing `requirements*.txt` or pytest layout, confirm the workflow still invokes the canonical command above (or an equivalent documented in the workflow file).

## `tests/` vs `tests/simple_tests/`

| Area | Role |
|------|------|
| **`tests/`** | Primary automated suite (`conftest.py`, `test_*.py`). Default smoke command targets this tree. |
| **`tests/simple_tests/`** | Older / broader functional, bug, and UI experiments; may assume a running server or extra deps. Not part of the canonical `-q` smoke unless you opt in. |
| **`tests/simple_tests/functional_tests/`** | Own `pytest.ini` (valid **`[pytest]`** section + **`pythonpath = ../../..`** so imports like `services.*` resolve when cwd is this folder). Prove config is picked up: `cd tests/simple_tests/functional_tests` then `python -m pytest --collect-only -q`, or rely on `tests/test_simple_tests_pytest_ini.py`. |

## E2E

- Playwright: `tests/e2e/smoke.spec.ts`; `playwright.config.ts` uses `testDir: ./tests/e2e` and pins `webServer.env.DATABASE_URL` for a local SQLite E2E DB.
- npm scripts: see root `package.json` (`test:e2e`, etc.).

## Application entry for tests

- **`create_app`** lives in **`application/factory.py`** (import re-exported from **`app`** for backwards compatibility).
- **`wsgi.py`** continues to use `from app import app`.

## Further reading

- `tests/README.md` — tree overview (may include stale counts).
- `docs/README_DOCS.md` — project changelog + operational index.

## Regression focus

Period parsing (`time_period` + parser), upload duplicates + preview, dataset-aware templates, period-range filters + export, WinError 32 on Windows preview files.

**Period marker / `data_entries` filters:** rentang `start_period` / `end_period` dari request dipusatkan lewat `services.request_params.data_entries_period_marker_range_from_request` (dipanggil dari `services/entry_list_page.parse_entry_list_params_from_request` untuk jalur preview GET args, manajemen POST values, dan ekspor).
