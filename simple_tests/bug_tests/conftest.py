"""
Konfigurasi pytest untuk bug tests - BPS Data Management System
Testing untuk edge cases, security vulnerabilities, dan error handling
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import konfigurasi dari parent directory
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))  # Add project root to path

from test_config import APP_CONFIG, TEST_DATA, PATHS, ensure_directories


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

    with app.app.test_client() as client:
        yield client

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


@pytest.fixture(scope="function")
def large_excel_file():
    """Create a large Excel file for testing file size limits"""
    import pandas as pd
    import tempfile

    # Create a large dataframe (should exceed 16MB limit)
    data = []
    for i in range(50000):  # Large number of rows
        data.append({
            'Indicator': f'Indicator_{i}',
            '2024-01': i * 1.5,
            '2024-02': i * 2.0,
            '2024-03': i * 2.5,
        })

    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df.to_excel(f.name, index=False)
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture(scope="function")
def malicious_file():
    """Create a file with malicious content for security testing"""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        # Create a basic Excel file with potentially malicious content
        import pandas as pd
        df = pd.DataFrame({
            'Indicator': ['<script>alert("XSS")</script>', "'; DROP TABLE users; --"],
            '2024-01': [100, 200]
        })
        df.to_excel(f.name, index=False)
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture(scope="function")
def invalid_file():
    """Create an invalid file for testing"""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"This is not an Excel file")
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass