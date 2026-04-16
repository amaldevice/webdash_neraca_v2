# Repository Guidelines

**Project state & docs map:** read [docs/README_DOCS.md](../docs/README_DOCS.md) and [README.md](../README.md).

## Project Structure & Module Organization
Core backend code lives at the repository root: `app.py` (Flask factory + `create_app`), paket **`excel_parser/`** (normalisasi, layout, payload parse), and the **`models/`** package (SQLite: `connection`, `queries`, `mutations`, `browse`, `data_filters`). HTTP routes are registered from the **`routes/`** package (`pages.py`, `upload_routes.py`, `manage.py`) via `register_routes`. Business logic sits under **`services/`** (e.g. `upload_flow`, `upload_preview`, `dataset_catalog`, `template_service`, `data_management_actions`, `period_comparisons`). `aggregator.py` has been removed; cache aggregation layer is no longer used. UI templates are in `templates/` with reusable fragments in `templates/partials/`. Static assets are under `static/` and Tailwind source is in `assets/tailwind.css`. Runtime upload files go to `uploads/` (including disk-backed preview sessions under `uploads/_preview_sessions/`). Primary automated tests are in `tests/`; browser smoke E2E is in **`e2e/`** (Playwright + POM). Tailwind/npm for CSS may use **`metadata/package.json`** separately from root **`package.json`** (Playwright).

## Build, Test, and Development Commands
- `python -m venv .venv; .\.venv\Scripts\activate` creates/activates local env (Windows).
- `pip install -r requirements.txt` installs Flask, pandas, and related deps; `pip install -r requirements-dev.txt` adds pytest.
- `python app.py` starts the app locally (default `http://localhost:5000`).
- `python -c "from models import init_db; init_db()"` initializes SQLite tables.
- `pytest` or `python -m pytest tests -q` runs the Python suite.
- **E2E:** from repo root `npm ci && npx playwright install chromium && npm run test:e2e` (Flask is started by `playwright.config.ts` `webServer`).
- `python -m py_compile app.py` plus paket `excel_parser/` / `models/` bila perlu untuk syntax checks.
- `npm install && npm run build:css` from **`metadata/`** compiles Tailwind CSS into `static/css/tailwind.css` when using that layout.
- `scripts/playwright_cli_smoke.ps1` — optional agent smoke using `@playwright/cli` (separate from `@playwright/test`).

## Coding Style & Naming Conventions
Use 4-space indentation and keep Python lines near 120 chars max. Prefer descriptive module/function names tied to domain behavior (avoid generic `utils`). Keep route handlers thin and move parsing/database logic into dedicated helpers. For templates, extend `templates/base_tailwind.html` and place reusable snippets in `templates/partials/_*.html`.

## Testing Guidelines
Use `pytest` for backend changes. Name tests as `test_<feature>.py` and functions as `test_<behavior>`. Targeted modules: `tests/test_routes.py`, `tests/test_models.py`, `tests/test_upload_flow.py`, `tests/test_excel_parser.py`, etc. For browser regression, run **`npm run test:e2e`**. Legacy `simple_tests/` may still reference older layouts; prefer `tests/` for new work.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commit style with scope, e.g. `feat(ui): refine controls` and `refactor(ui): modularize ...`. Continue using `type(scope): summary` (`feat`, `fix`, `refactor`, `test`, `docs`). PRs should include: purpose, key changes, test commands run (`pytest`, `playwright test` if UI touched), linked issue/task, and before/after screenshots for UI changes. Keep PRs focused by feature area (for example, one page/module family per PR).

## Security & Configuration Tips
Do not commit real data exports or secrets. Configure `FLASK_SECRET_KEY` via environment variables for non-local environments. Validate uploaded file types and preserve existing input-validation patterns when adding routes/forms.
