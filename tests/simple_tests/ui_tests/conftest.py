"""Konfigurasi pytest untuk UI Tests"""

import pytest
import importlib.util
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "test_config.py"
spec = importlib.util.spec_from_file_location("_simple_tests_test_config", CONFIG_PATH)
if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
    raise RuntimeError("Unable to load local test_config module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

APP_CONFIG = module.APP_CONFIG
CHROME_CONFIG = module.CHROME_CONFIG
PATHS = module.PATHS

@pytest.fixture(scope="session", autouse=True)
def setup_chrome_devtools():
    """Setup Chrome DevTools untuk testing session"""
    try:
        # Initialize Chrome DevTools connection
        # Note: In real implementation, this would establish connection to Chrome DevTools
        print("🔧 Setting up Chrome DevTools for testing...")

        # Configure browser settings
        print(f"📐 Window size: {CHROME_CONFIG['window_size']['width']}x{CHROME_CONFIG['window_size']['height']}")
        print(f"🎯 Base URL: {APP_CONFIG['base_url']}")
        print(f"📸 Screenshots: {'Enabled' if PATHS.get('capture_screenshots', True) else 'Disabled'}")

        yield

    except Exception as e:
        print(f"❌ Chrome DevTools setup failed: {e}")
        raise
    finally:
        print("🧹 Cleaning up Chrome DevTools session...")

@pytest.fixture(scope="function")
def browser_page():
    """Fixture untuk setup halaman browser baru per test"""
    # In real implementation, this would create a new page/tab
    print("📄 Setting up new browser page for test...")

    yield

    # Cleanup after test
    print("🗑️ Cleaning up browser page...")

@pytest.fixture(scope="function")
def screenshot_helper():
    """Helper fixture untuk capture screenshot dengan timestamp"""
    def take_screenshot(name):
        """Capture screenshot dengan nama tertentu"""
        try:
            # In real implementation, this would call Chrome DevTools screenshot API
            print(f"📸 Taking screenshot: {name}")
            return True
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")
            return False

    return take_screenshot

# Pytest configuration
def pytest_configure(config):
    """Konfigurasi pytest untuk UI tests"""
    config.addinivalue_line(
        "markers", "ui: mark test as UI test using browser automation"
    )
    config.addinivalue_line(
        "markers", "chrome: mark test as using Chrome DevTools MCP"
    )
    config.addinivalue_line(
        "markers", "visual: mark test as visual regression test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection untuk UI tests"""
    for item in items:
        # Add UI marker to all tests in ui_tests directory
        if "ui_tests" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
            item.add_marker(pytest.mark.chrome)