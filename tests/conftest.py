import importlib
import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so `import app` / `import models` works when
# pytest is invoked from anywhere.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Default test DB: set before ``import models`` so ``config`` dotenv (override=False)
# cannot point the suite at a remote MySQL/PostgreSQL from `.env`.
# Opt out for remote dialect smoke: ``USE_ENV_DATABASE_URL_FOR_TESTS=1`` + ``DATABASE_URL=mysql+...``.
_DEFAULT_PYTEST_DB = ROOT / ".pytest_runtime_default.sqlite3"
_use_env_db = os.environ.get("USE_ENV_DATABASE_URL_FOR_TESTS", "").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
if not _use_env_db:
    os.environ["DATABASE_URL"] = f"sqlite:///{_DEFAULT_PYTEST_DB.resolve().as_posix()}"

import models


def pytest_configure(config) -> None:  # noqa: ANN001
    """Bind SQLAlchemy engine to ``DATABASE_URL`` (already defaulted to in-repo SQLite unless opted out)."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        url = f"sqlite:///{_DEFAULT_PYTEST_DB.resolve().as_posix()}"
        os.environ["DATABASE_URL"] = url
    if url.startswith("sqlite:"):
        models.DB_PATH = str(_DEFAULT_PYTEST_DB)
    from infrastructure.db import dispose_engine, init_engine

    dispose_engine()
    init_engine(url)
    models.init_db()


def pytest_runtest_teardown(item, nextitem) -> None:  # noqa: ANN001, ARG001
    """If a test left SQLAlchemy disposed, re-bind default SQLite (avoids order-dependent failures)."""
    from infrastructure.db import dispose_engine, init_engine, is_engine_initialized

    if is_engine_initialized():
        return
    p = _DEFAULT_PYTEST_DB
    url = f"sqlite:///{p.resolve().as_posix()}"
    os.environ["DATABASE_URL"] = url
    models.DB_PATH = str(p)
    dispose_engine()
    init_engine(url)
    models.init_db()


@pytest.fixture
def database_url() -> str | None:
    """Explicit ``DATABASE_URL`` from env (empty → ``None``)."""
    raw = os.environ.get("DATABASE_URL", "").strip()
    return raw or None


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    path_str = str(db_file)
    monkeypatch.setattr(models, "DB_PATH", path_str)
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    from infrastructure.db import dispose_engine, init_engine

    dispose_engine()
    init_engine(url)
    models.init_db()
    return db_file


@pytest.fixture
def app_module(db_path):
    import app as app_module

    importlib.reload(app_module)
    app_module.app = app_module.create_app(testing=True)
    return app_module


@pytest.fixture
def client(app_module):
    with app_module.app.test_client() as client:
        yield client
