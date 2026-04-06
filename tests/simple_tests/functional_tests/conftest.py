"""
Konfigurasi pytest untuk functional tests
"""

import importlib.util
import os
import tempfile
from pathlib import Path

from flask.testing import FlaskClient
from werkzeug.datastructures import MultiDict

import pytest


def _load_test_config():
    """Load test_config from local test package."""
    config_path = Path(__file__).resolve().parent.parent / "test_config.py"
    spec = importlib.util.spec_from_file_location(
        "_simple_tests_test_config", config_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load local test_config module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_TEST_CONFIG = _load_test_config()

APP_CONFIG = _TEST_CONFIG.APP_CONFIG
TEST_DATA = _TEST_CONFIG.TEST_DATA
PATHS = _TEST_CONFIG.PATHS
ensure_directories = _TEST_CONFIG.ensure_directories


class LegacyCompatTestClient(FlaskClient):
    """Small compatibility shim for legacy ``data_file`` uploads."""

    def post(self, *args, data=None, data_file=None, **kwargs):
        if data_file is not None:
            request_data = {}
            if data is not None:
                if isinstance(data, MultiDict):
                    request_data = {k: v for k, v in data.to_dict().items()}
                else:
                    request_data = dict(data)
            if "action" not in request_data:
                request_data["action"] = "save"
            if "excel_file" not in request_data:
                request_data["excel_file"] = data_file
            data = request_data
            kwargs.setdefault("content_type", "multipart/form-data")
        return super().post(*args, data=data, **kwargs)


@pytest.fixture(scope="session")
def app_config():
    """Konfigurasi aplikasi untuk testing"""
    return APP_CONFIG


@pytest.fixture(scope="session")
def test_data():
    """Data test yang dapat digunakan di semua test"""
    return TEST_DATA


@pytest.fixture(scope="session")
def temp_db_path():
    """Path untuk database temporary testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name

    yield temp_path

    # Cleanup setelah test selesai
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture(scope="function")
def test_client(temp_db_path):
    """Test client untuk Flask app dengan database temporary"""
    # Set database path untuk testing
    import models
    original_db_path = models.DB_PATH
    models.DB_PATH = temp_db_path

    # Reinitialize database
    models.init_db()

    # Import app setelah database path diubah
    import app
    app.app.config['TESTING'] = True

    original_client_class = app.app.test_client_class
    app.app.test_client_class = LegacyCompatTestClient
    client = app.app.test_client()
    yield client
    app.app.test_client_class = original_client_class

    # Restore original database path
    models.DB_PATH = original_db_path


@pytest.fixture(scope="function")
def sample_data_entries():
    """Sample data entries untuk testing"""
    return [
        {
            "uploader_name": "Alice",
            "version": "v1.0",
            "template_type": "manual",
            "data_type": "flow",
            "time_period": "monthly",
            "indicator_name": "GDP",
            "value": 100.5,
            "unit": None,
            "region_code": None,
            "year": 2024,
            "month": 1,
            "quarter": 1,
            "created_at": "2024-01-01T10:00:00"
        },
        {
            "uploader_name": "Bob",
            "version": "v1.1",
            "template_type": "manual",
            "data_type": "stock",
            "time_period": "quarterly",
            "indicator_name": "Inflation",
            "value": 250.0,
            "unit": None,
            "region_code": None,
            "year": 2024,
            "month": None,
            "quarter": 2,
            "created_at": "2024-02-01T10:00:00"
        },
        {
            "uploader_name": "Charlie",
            "version": "v1.2",
            "template_type": "manual",
            "data_type": "flow",
            "time_period": "yearly",
            "indicator_name": "Population",
            "value": 150.75,
            "unit": None,
            "region_code": None,
            "year": 2024,
            "month": None,
            "quarter": None,
            "created_at": "2024-03-01T10:00:00"
        }
    ]


@pytest.fixture(scope="function")
def populated_db(test_client, sample_data_entries):
    """Database yang sudah terisi dengan sample data"""
    import models
    # Clear any existing data first to avoid conflicts
    models.clear_all_data()
    models.insert_entries(sample_data_entries)

    # Refresh aggregated summary
    from aggregator import refresh_aggregated_summary
    refresh_aggregated_summary()

    return test_client