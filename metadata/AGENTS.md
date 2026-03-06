# Repository Guidelines

## Project Structure & Module Organization
Core backend code lives at the repository root: `app.py` (Flask routes), `models.py` (SQLite access), `excel_parser.py` (ingestion/normalization), and `aggregator.py` (summary cache logic). UI templates are in `templates/` with reusable fragments in `templates/partials/`. Static assets are under `static/` and Tailwind source is in `assets/tailwind.css`. Runtime upload files go to `uploads/`. Primary automated tests are in `tests/`; lightweight functional/UI/bug suites are in `simple_tests/`.

## Build, Test, and Development Commands
- `python -m venv .venv; .\.venv\Scripts\activate` creates/activates local env (Windows).
- `pip install -r requirements.txt` installs Flask, pandas, pytest, and related deps.
- `python app.py` starts the app locally (default `http://localhost:5000`).
- `python -c "from models import init_db; init_db()"` initializes SQLite tables.
- `pytest` runs the main test suite in `tests/`.
- `python -m py_compile app.py models.py excel_parser.py aggregator.py` performs syntax checks.
- `npm install && npm run build:css` compiles Tailwind CSS into `static/css/tailwind.css`.
- `npm run watch:css` rebuilds CSS during frontend edits.

## Coding Style & Naming Conventions
Use 4-space indentation and keep Python lines near 120 chars max. Prefer descriptive module/function names tied to domain behavior (avoid generic `utils`). Keep route handlers thin and move parsing/database logic into dedicated helpers. For templates, extend `templates/base_tailwind.html` and place reusable snippets in `templates/partials/_*.html`.

## Testing Guidelines
Use `pytest` for all new backend changes. Name tests as `test_<feature>.py` and functions as `test_<behavior>`. Add/update targeted tests in `tests/test_routes.py`, `tests/test_models.py`, or `tests/test_app_utils.py` based on change scope. For user-flow or UI-impacting work, run `python simple_tests/run_tests.py --test functional` (or `--test ui`) with the app running.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commit style with scope, e.g. `feat(ui): refine controls` and `refactor(ui): modularize ...`. Continue using `type(scope): summary` (`feat`, `fix`, `refactor`, `test`, `docs`). PRs should include: purpose, key changes, test commands run, linked issue/task, and before/after screenshots for UI changes. Keep PRs focused by feature area (for example, one page/module family per PR).

## Security & Configuration Tips
Do not commit real data exports or secrets. Configure `FLASK_SECRET_KEY` via environment variables for non-local environments. Validate uploaded file types and preserve existing input-validation patterns when adding routes/forms.
