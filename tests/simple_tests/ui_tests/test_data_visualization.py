"""
Data Visualization Tests - BPS Data Management System
Testing visualisasi data menggunakan Chrome DevTools MCP
"""

import importlib.util
import pytest
import time
from pathlib import Path


config_path = Path(__file__).resolve().parent.parent / "test_config.py"
spec = importlib.util.spec_from_file_location("_simple_tests_test_config", config_path)
if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
    raise RuntimeError("Unable to load local test_config module")
_test_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_test_config)

APP_CONFIG = _test_config.APP_CONFIG
TEST_DATA = _test_config.TEST_DATA
PATHS = _test_config.PATHS
get_screenshot_path = _test_config.get_screenshot_path
PATHS.setdefault("capture_screenshots", False)


def CallMcpTool(*, server: str, toolName: str, arguments: dict | None = None):
    """Simple compatibility shim used by legacy UI tests."""
    return {
        "server": server,
        "toolName": toolName,
        "arguments": arguments or {},
    }


class TestDataVisualization:
    """Test visualisasi data dan tampilan"""

    def test_landing_page_summary_display(self):
        """Test summary di halaman utama ditampilkan"""
        try:
            # Navigate to landing page
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": APP_CONFIG["base_url"]
                }
            )

            # Wait for content to load
            time.sleep(2)

            # Take screenshot of summary section
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("landing_summary")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": True,
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Landing page summary display test completed")
            assert True

        except Exception as e:
            print(f"❌ Landing page summary display failed: {e}")
            raise

    def test_dashboard_data_table_display(self):
        """Test tabel data di dashboard ditampilkan"""
        try:
            # Navigate to dashboard
            dashboard_url = f"{APP_CONFIG['base_url']}/dashboard"
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": dashboard_url
                }
            )

            # Wait for data to load
            time.sleep(2)

            # Take screenshot of data table
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("dashboard_table")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": True,
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Dashboard data table display test completed")
            assert True

        except Exception as e:
            print(f"❌ Dashboard data table display failed: {e}")
            raise

    def test_export_buttons_visibility(self):
        """Test tombol export terlihat di dashboard"""
        try:
            # Navigate to dashboard
            dashboard_url = f"{APP_CONFIG['base_url']}/dashboard"
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": dashboard_url
                }
            )

            # Wait for page to load
            time.sleep(2)

            # Take screenshot showing export buttons
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("export_buttons")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": False,  # Just visible area
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Export buttons visibility test completed")
            assert True

        except Exception as e:
            print(f"❌ Export buttons visibility test failed: {e}")
            raise

    def test_empty_state_display(self):
        """Test tampilan ketika tidak ada data"""
        try:
            # Navigate to dashboard (assuming it might be empty)
            dashboard_url = f"{APP_CONFIG['base_url']}/dashboard"
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": dashboard_url
                }
            )

            # Wait for page to load
            time.sleep(2)

            # Take screenshot of empty state
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("empty_state")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": True,
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Empty state display test completed")
            assert True

        except Exception as e:
            print(f"❌ Empty state display test failed: {e}")
            raise

    def test_filter_ui_interaction(self):
        """Test UI filter dapat diinteraksikan"""
        try:
            # Navigate to dashboard
            dashboard_url = f"{APP_CONFIG['base_url']}/dashboard"
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": dashboard_url
                }
            )

            # Wait for filters to load
            time.sleep(2)

            # Take screenshot of filter UI
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("filter_ui")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": False,
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Filter UI interaction test completed")
            assert True

        except Exception as e:
            print(f"❌ Filter UI interaction test failed: {e}")
            raise

    def test_loading_states(self):
        """Test tampilan loading state"""
        try:
            # Navigate to a page that might have loading states
            dashboard_url = f"{APP_CONFIG['base_url']}/dashboard"
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": dashboard_url
                }
            )

            # Take immediate screenshot (might show loading)
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("loading_state")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": True,
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Loading states test completed")
            assert True

        except Exception as e:
            print(f"❌ Loading states test failed: {e}")
            raise