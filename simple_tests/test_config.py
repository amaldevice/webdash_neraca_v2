"""
Konfigurasi testing untuk BPS Data Management System
Testing sederhana untuk tim internal
"""

import os
from pathlib import Path

# Base configuration
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

# Application settings
APP_CONFIG = {
    "base_url": "http://localhost:5000",
    "timeout": 10,  # seconds
    "max_retries": 3,
}

# Test data
TEST_DATA = {
    "uploaders": ["Alice", "Bob", "Charlie"],
    "data_types": ["flow", "stock"],
    "time_periods": ["monthly", "quarterly", "yearly"],
    "indicators": ["GDP", "Inflation", "Population"],
    "sample_values": [100.5, 250.0, 75.25, 150.75],
}

# File paths
PATHS = {
    "screenshots": BASE_DIR / "screenshots",
    "test_results": BASE_DIR / "test_results",
    "test_data": BASE_DIR / "test_data",
    "uploads": PROJECT_ROOT / "uploads",
}

# Chrome DevTools settings
CHROME_CONFIG = {
    "headless": False,  # Set to True for CI/CD
    "window_size": {"width": 1280, "height": 720},
    "default_wait": 2000,  # milliseconds
}

# Test settings
TEST_SETTINGS = {
    "capture_screenshots": True,
    "verbose_output": True,
    "cleanup_after_test": True,
}

def ensure_directories():
    """Create necessary directories for testing"""
    for path in PATHS.values():
        path.mkdir(parents=True, exist_ok=True)

def get_test_excel_path():
    """Get path to test Excel file"""
    return PATHS["test_data"] / "sample_data.xlsx"

def get_screenshot_path(test_name):
    """Generate screenshot path for test"""
    return PATHS["screenshots"] / f"{test_name}_{get_timestamp()}.png"

def get_timestamp():
    """Get current timestamp for file naming"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Initialize directories on import
ensure_directories()