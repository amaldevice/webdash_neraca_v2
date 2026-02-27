#!/usr/bin/env python3
"""
Simple Test Runner - BPS Data Management System
Runner script untuk menjalankan semua jenis testing
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_config import APP_CONFIG, PATHS

class TestRunner:
    """Runner untuk semua jenis testing"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.project_root = self.base_dir.parent
        self.start_time = None
        self.test_results = {}

    def check_prerequisites(self):
        """Cek prasyarat sebelum menjalankan test"""
        print("Checking prerequisites...")

        # Check if Flask app is running
        try:
            import requests
            response = requests.get(APP_CONFIG["base_url"], timeout=5)
            if response.status_code == 200:
                print("SUCCESS: Flask app is running")
            else:
                print(f"WARNING: Flask app returned status {response.status_code}")
        except:
            print("ERROR: Flask app is not accessible")
            print("   Please start the app with: python app.py")
            return False

        # Check if test directories exist
        required_dirs = ["functional_tests", "ui_tests", "bug_tests"]
        for dir_name in required_dirs:
            if not (self.base_dir / dir_name).exists():
                print(f"ERROR: Test directory missing: {dir_name}")
                return False

        print("SUCCESS: All prerequisites met")
        return True

    def run_functional_tests(self, verbose=False, html_report=False):
        """Jalankan functional tests dengan qa-agent"""
        print("\nRunning Functional Tests (qa-agent)...")

        cmd = ["python", "-m", "pytest", "functional_tests/"]
        if verbose:
            cmd.append("-v")
        if html_report:
            cmd.extend(["--html=test_results/functional_report.html", "--self-contained-html"])

        result = self._run_command(cmd, cwd=self.base_dir)
        self.test_results["functional"] = result
        return result

    def run_ui_tests(self, verbose=False):
        """Jalankan UI tests dengan Chrome DevTools MCP"""
        print("\nRunning UI Tests (Chrome DevTools)...")

        cmd = ["python", "-m", "pytest", "ui_tests/"]
        if verbose:
            cmd.append("-v")

        result = self._run_command(cmd, cwd=self.base_dir)
        self.test_results["ui"] = result
        return result

    def run_bug_tests(self, verbose=False):
        """Jalankan bug tests dengan bug-hunter"""
        print("\nRunning Bug Tests (bug-hunter)...")

        cmd = ["python", "-m", "pytest", "bug_tests/"]
        if verbose:
            cmd.append("-v")

        result = self._run_command(cmd, cwd=self.base_dir)
        self.test_results["bug"] = result
        return result

    def run_all_tests(self, verbose=False, html_report=False):
        """Jalankan semua jenis test"""
        print("Starting Complete Test Suite...")

        if not self.check_prerequisites():
            return False

        self.start_time = time.time()

        # Run all test suites
        results = []
        results.append(self.run_functional_tests(verbose, html_report))
        results.append(self.run_ui_tests(verbose))
        results.append(self.run_bug_tests(verbose))

        # Generate summary
        self.generate_summary(results)

        return all(results)

    def run_specific_test(self, test_type, verbose=False):
        """Jalankan test spesifik"""
        if not self.check_prerequisites():
            return False

        self.start_time = time.time()

        if test_type == "functional":
            result = self.run_functional_tests(verbose)
        elif test_type == "ui":
            result = self.run_ui_tests(verbose)
        elif test_type == "bug":
            result = self.run_bug_tests(verbose)
        else:
            print(f"❌ Unknown test type: {test_type}")
            return False

        return result

    def _run_command(self, cmd, cwd=None):
        """Jalankan command dan return success status"""
        try:
            print(f"📋 Command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                print("SUCCESS: Test completed successfully")
                if result.stdout:
                    print(result.stdout)
            else:
                print("FAILED: Test failed")
                if result.stderr:
                    print("STDERR:", result.stderr)
                if result.stdout:
                    print("STDOUT:", result.stdout)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("TIMEOUT: Test timed out")
            return False
        except Exception as e:
            print(f"ERROR: Error running test: {e}")
            return False

    def generate_summary(self, results):
        """Generate test summary"""
        duration = time.time() - self.start_time

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        print(f"⏱️  Total Duration: {duration:.2f} seconds")
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Test results
        print("\n📈 Test Results:")
        test_types = ["functional", "ui", "bug"]
        for i, test_type in enumerate(test_types):
            status = "✅ PASS" if results[i] else "❌ FAIL"
            print(f"   {test_type.capitalize()} Tests: {status}")

        # Overall status
        overall_pass = all(results)
        print(f"\nOverall Status: {'ALL TESTS PASSED' if overall_pass else 'SOME TESTS FAILED'}")

        # Recommendations
        if not overall_pass:
            print("\nRecommendations:")
            if not results[0]:  # functional failed
                print("   - Check functional_tests/ for assertion failures")
            if not results[1]:  # ui failed
                print("   - Check ui_tests/ and screenshots/ for UI issues")
            if not results[2]:  # bug failed
                print("   - Check bug_tests/ for security/vulnerability issues")

        print("\nCheck these directories for detailed results:")
        print(f"   - Test Results: {PATHS['test_results']}")
        print(f"   - Screenshots: {PATHS['screenshots']}")
        print(f"   - Functional Tests: {self.base_dir}/functional_tests/")
        print(f"   - UI Tests: {self.base_dir}/ui_tests/")
        print(f"   - Bug Tests: {self.base_dir}/bug_tests/")

        print("="*60)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Simple Test Runner for BPS Data Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --test functional  # Run only functional tests
  python run_tests.py --verbose          # Run with verbose output
  python run_tests.py --html-report      # Generate HTML report
  python run_tests.py --help            # Show this help
        """
    )

    parser.add_argument(
        "--test",
        choices=["functional", "ui", "bug"],
        help="Run specific test type (default: all)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML report for functional tests"
    )

    args = parser.parse_args()

    # Initialize test runner
    runner = TestRunner()

    # Run tests based on arguments
    if args.test:
        success = runner.run_specific_test(args.test, args.verbose)
    else:
        success = runner.run_all_tests(args.verbose, args.html_report)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()