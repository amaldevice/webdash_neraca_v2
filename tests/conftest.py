import importlib
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so `import app` / `import models` works when
# pytest is invoked from anywhere.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import models


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(models, "DB_PATH", str(db_file))
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
