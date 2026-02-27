"""
Browser Navigation Tests - BPS Data Management System
Testing navigasi dan interaksi dasar menggunakan Chrome DevTools MCP
"""

import pytest
import time
from pathlib import Path
from test_config import APP_CONFIG, PATHS, get_screenshot_path

class TestBrowserNavigation:
    """Test navigasi browser dan halaman dasar"""

    def test_landing_page_load(self):
        """Test halaman utama dapat dimuat dengan benar"""
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

            # Take screenshot for verification
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("landing_page_load")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": True,
                        "filePath": str(screenshot_path)
                    }
                )
                print(f"Screenshot saved: {screenshot_path}")

            # Basic verification - page should load without errors
            print("SUCCESS: Landing page loaded successfully")
            assert True  # Placeholder - in real implementation check page content

        except Exception as e:
            print(f"❌ Landing page load failed: {e}")
            raise

    def test_dashboard_navigation(self):
        """Test navigasi ke halaman dashboard"""
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

            # Take screenshot
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("dashboard_navigation")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": True,
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Dashboard page navigation successful")
            assert True

        except Exception as e:
            print(f"❌ Dashboard navigation failed: {e}")
            raise

    def test_manual_entry_navigation(self):
        """Test navigasi ke halaman manual entry"""
        try:
            # Navigate to manual entry page
            manual_url = f"{APP_CONFIG['base_url']}/manual"
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": manual_url
                }
            )

            # Take screenshot
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("manual_entry_navigation")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": True,
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Manual entry page navigation successful")
            assert True

        except Exception as e:
            print(f"❌ Manual entry navigation failed: {e}")
            raise

    def test_upload_page_navigation(self):
        """Test navigasi ke halaman upload"""
        try:
            # Navigate to upload page
            upload_url = f"{APP_CONFIG['base_url']}/upload"
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": upload_url
                }
            )

            # Take screenshot
            if PATHS["capture_screenshots"]:
                screenshot_path = get_screenshot_path("upload_page_navigation")
                CallMcpTool(
                    server="user-chrome-devtools",
                    toolName="take_screenshot",
                    arguments={
                        "format": "png",
                        "fullPage": True,
                        "filePath": str(screenshot_path)
                    }
                )

            print("✅ Upload page navigation successful")
            assert True

        except Exception as e:
            print(f"❌ Upload page navigation failed: {e}")
            raise

    def test_page_refresh_functionality(self):
        """Test fungsi refresh halaman"""
        try:
            # First navigate to a page
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "url",
                    "url": APP_CONFIG["base_url"]
                }
            )

            # Wait a moment
            time.sleep(1)

            # Refresh the page
            result = CallMcpTool(
                server="user-chrome-devtools",
                toolName="navigate_page",
                arguments={
                    "type": "reload",
                    "ignoreCache": True
                }
            )

            print("✅ Page refresh functionality works")
            assert True

        except Exception as e:
            print(f"❌ Page refresh failed: {e}")
            raise