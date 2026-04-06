#!/usr/bin/env python3
"""
Script untuk menjalankan functional tests BPS Data Management System

Usage:
    python run_tests.py                    # Jalankan semua tests
    python run_tests.py --verbose          # Dengan output verbose
    python run_tests.py --coverage         # Dengan coverage report
    python run_tests.py --html-report      # Generate HTML report
    python run_tests.py --test landing     # Jalankan hanya landing page tests
    python run_tests.py --benchmark        # Performance benchmark
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Ensure we're in the right directory
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

def run_command(cmd, cwd=None, capture_output=False):
    """Run shell command dengan proper error handling"""
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd or SCRIPT_DIR,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def check_prerequisites():
    """Check bahwa prerequisites terinstall"""
    try:
        import pytest
        import requests
        import pandas
        import bs4
        print("SUCCESS: Prerequisites check passed")
    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        print("Please install requirements:")
        print("pip install -r requirements.txt")
        sys.exit(1)

def check_app_running():
    """Check bahwa Flask app sedang running"""
    import requests
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: Flask app is running")
            return True
        else:
            print(f"⚠️  Flask app returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("ERROR: Flask app is not running")
        print("Please start the app first:")
        print("cd /path/to/project && python app.py")
        return False

def get_test_files():
    """Get list of test files"""
    return [
        "test_landing_page.py",
        "test_upload_excel.py",
        "test_manual_entry.py",
        "test_dashboard.py",
        "test_export.py"
    ]

def build_pytest_command(args):
    """Build pytest command berdasarkan arguments"""
    cmd = [sys.executable, "-m", "pytest"]

    # Test selection
    if args.test:
        test_name = args.test.lower()
        test_mapping = {
            'landing': 'test_landing_page.py',
            'upload': 'test_upload_excel.py',
            'manual': 'test_manual_entry.py',
            'dashboard': 'test_dashboard.py',
            'export': 'test_export.py'
        }

        if test_name in test_mapping:
            cmd.append(test_mapping[test_name])
        else:
            print(f"ERROR: Unknown test: {test_name}")
            print(f"Available: {', '.join(test_mapping.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        cmd.extend(get_test_files())

    # Options
    if args.verbose or args.v:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if args.html_report:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])

    if args.coverage:
        cmd.extend([
            f"--cov={PROJECT_ROOT}",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])

    if args.benchmark:
        try:
            import pytest_benchmark
            cmd.extend([
                "--benchmark-only",
                "--benchmark-columns=min,max,mean,stddev",
                "--benchmark-sort=mean"
            ])
        except ImportError:
            print("WARNING: pytest-benchmark not installed")
            print("Install with: pip install pytest-benchmark")
            sys.exit(1)

    if args.fail_fast:
        cmd.append("--tb=short")
        cmd.append("-x")

    if args.parallel:
        try:
            # Check if pytest-xdist available
            import xdist
            cmd.extend(["-n", str(args.parallel)])
        except ImportError:
            print("⚠️  pytest-xdist not installed, running sequentially")
            print("Install with: pip install pytest-xdist")

    return cmd

def main():
    parser = argparse.ArgumentParser(description="Run BPS Data Management Functional Tests")
    parser.add_argument("--test", choices=['landing', 'upload', 'manual', 'dashboard', 'export'],
                       help="Run specific test suite")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("--html-report", action="store_true",
                       help="Generate HTML report")
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report")
    parser.add_argument("--benchmark", action="store_true",
                       help="Run performance benchmarks")
    parser.add_argument("--fail-fast", action="store_true",
                       help="Stop on first failure")
    parser.add_argument("--parallel", type=int, metavar="N",
                       help="Run tests in parallel with N workers")
    parser.add_argument("--skip-checks", action="store_true",
                       help="Skip prerequisite checks")

    args = parser.parse_args()

    print("BPS Data Management - Functional Tests")
    print("=" * 50)

    # Change to script directory
    os.chdir(SCRIPT_DIR)

    # Prerequisites check
    if not args.skip_checks:
        print("\n📋 Checking prerequisites...")
        check_prerequisites()

        print("\nChecking Flask app...")
        if not check_app_running():
            sys.exit(1)

    # Build and run pytest command
    print("\nRunning tests...")
    cmd = build_pytest_command(args)

    try:
        result = run_command(cmd)

        print("\nSUCCESS: Tests completed successfully!")

        if args.html_report:
            print("📊 HTML report generated: test_report.html")

        if args.coverage:
            print("Coverage report generated: htmlcov/index.html")

    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Tests failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()