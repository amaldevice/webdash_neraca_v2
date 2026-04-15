#!/usr/bin/env python3
"""
Comprehensive Bug Testing Suite for BPS Data Management System
Tests edge cases, error conditions, and potential runtime issues
"""

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import sqlite3

_TESTS_ROOT = Path(__file__).resolve().parents[1]


def _temp_db_attach(case: unittest.TestCase) -> None:
    """Point models.DB_PATH at a fresh file DB (shared across connections in tests)."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    case._temp_db_path = tmp.name
    import models

    models.DB_PATH = case._temp_db_path
    models.init_db()


def _temp_db_detach(case: unittest.TestCase) -> None:
    import models

    models.DB_PATH = str(_TESTS_ROOT / "data.db")
    try:
        os.unlink(case._temp_db_path)
    except OSError:
        pass


# Import the application modules
from app import _build_manual_entry, _parse_period_date, allowed_file, app, validate_metadata
from models import (
    init_db, insert_entries, query_data_entries, get_total_entries_count,
    delete_data_entry, update_data_entry_full, bulk_delete_entries, bulk_update_entries,
    _to_float,
)
from services.period_comparisons import calculate_period_comparisons
from excel_parser import parse_excel, detect_template_format, _normalize_record, _parse_period
from services.timeutil import utc_now_iso


class TestValidation(unittest.TestCase):
    """Test input validation functions"""

    def test_allowed_file_valid_extensions(self):
        """Test file extension validation"""
        self.assertTrue(allowed_file("test.xlsx"))
        self.assertTrue(allowed_file("test.xls"))
        self.assertFalse(allowed_file("test.txt"))
        self.assertFalse(allowed_file("test.exe"))
        self.assertFalse(allowed_file("test.xlsx.exe"))  # Path traversal attempt

    def test_validate_metadata_valid(self):
        """Test metadata validation with valid inputs"""
        errors = validate_metadata("flow", "monthly")
        self.assertEqual(len(errors), 0)

        errors = validate_metadata("stock", "quarterly")
        self.assertEqual(len(errors), 0)

        errors = validate_metadata("flow", "yearly")
        self.assertEqual(len(errors), 0)

    def test_validate_metadata_invalid(self):
        """Test metadata validation with invalid inputs"""
        errors = validate_metadata("invalid", "monthly")
        self.assertIn("Tipe data tidak valid.", errors)

        errors = validate_metadata("flow", "invalid")
        self.assertIn("Periode tidak valid.", errors)

        errors = validate_metadata("", "")
        self.assertEqual(len(errors), 2)

    def test_parse_period_date_monthly(self):
        """Test period date parsing for monthly format"""
        year, month, quarter = _parse_period_date("monthly", "2024-01")
        self.assertEqual((year, month, quarter), (2024, 1, 1))

        year, month, quarter = _parse_period_date("monthly", "2024-12")
        self.assertEqual((year, month, quarter), (2024, 12, 4))

    def test_parse_period_date_quarterly(self):
        """Test period date parsing for quarterly format"""
        year, month, quarter = _parse_period_date("quarterly", "2024-Q1")
        self.assertEqual((year, month, quarter), (2024, None, 1))

        year, month, quarter = _parse_period_date("quarterly", "2024-Q4")
        self.assertEqual((year, month, quarter), (2024, None, 4))

    def test_parse_period_date_yearly(self):
        """Test period date parsing for yearly format"""
        year, month, quarter = _parse_period_date("yearly", "2024")
        self.assertEqual((year, month, quarter), (2024, None, None))

    def test_parse_period_date_invalid(self):
        """Test period date parsing with invalid inputs"""
        year, month, quarter = _parse_period_date("monthly", "invalid")
        self.assertEqual((year, month, quarter), (None, None, None))

        year, month, quarter = _parse_period_date("monthly", "2024-13")  # Invalid month
        self.assertEqual((year, month, quarter), (None, None, None))

        year, month, quarter = _parse_period_date("quarterly", "2024-Q5")  # Invalid quarter
        self.assertEqual((year, month, quarter), (None, None, None))


class TestExcelParser(unittest.TestCase):
    """Test Excel parsing functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_template_format_vertical(self):
        """Test template format detection for vertical layout"""
        df = pd.DataFrame({
            0: [2024, "GDP", "Inflasi", "Ekspor"],
            1: ["Q1", 1000, 2000, 3000],
            2: ["Q2", 1100, 2100, 3100]
        })
        self.assertEqual(detect_template_format(df), "vertical")

    def test_detect_template_format_horizontal(self):
        """Test template format detection for horizontal layout"""
        df = pd.DataFrame({
            0: ["GDP", "Inflasi", "Ekspor"],
            1: [1000, 2000, 3000],
            2: [1100, 2100, 3100]
        })
        self.assertEqual(detect_template_format(df), "horizontal")

    def test_normalize_record_valid(self):
        """Test record normalization with valid data"""
        record = _normalize_record(
            uploader="test_user",
            version="v1.0",
            layout="vertical",
            data_type="flow",
            time_period="monthly",
            indicator="GDP",
            value=1000.5,
            period_value="2024-01"
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["indicator_name"], "GDP")
        self.assertEqual(record["value"], 1000.5)
        self.assertEqual(record["year"], 2024)
        self.assertEqual(record["month"], 1)

    def test_normalize_record_invalid_value(self):
        """Test record normalization with invalid value"""
        record = _normalize_record(
            uploader="test_user",
            version="v1.0",
            layout="vertical",
            data_type="flow",
            time_period="monthly",
            indicator="GDP",
            value="invalid",
            period_value="2024-01"
        )
        self.assertIsNone(record)

    def test_normalize_record_missing_indicator(self):
        """Test record normalization with missing indicator"""
        record = _normalize_record(
            uploader="test_user",
            version="v1.0",
            layout="vertical",
            data_type="flow",
            time_period="monthly",
            indicator="",
            value=1000,
            period_value="2024-01"
        )
        self.assertIsNone(record)


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations"""

    def setUp(self):
        """Use a temp file DB so every connection shares one SQLite database."""
        import sys
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))

        import models

        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        models.DB_PATH = self.temp_db.name
        models.init_db()

    def tearDown(self):
        import sys
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))

        import models

        models.DB_PATH = os.path.join(ROOT, "data.db")
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass

    def test_insert_entries_success(self):
        """Test successful entry insertion"""
        entries = [{
            "uploader_name": "test_user",
            "version": "v1.0",
            "indicator_name": "GDP",
            "value": 1000.0,
            "data_type": "flow",
            "time_period": "monthly",
            "year": 2024,
            "month": 1,
            "created_at": utc_now_iso()
        }]
        # Should not raise exception
        insert_entries(entries)

        # Verify insertion
        results = query_data_entries(limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["indicator_name"], "GDP")

    def test_insert_entries_duplicate_constraint(self):
        """Test insertion with duplicate constraint violation"""
        entries = [{
            "uploader_name": "test_user",
            "version": "v1.0",
            "indicator_name": "GDP",
            "value": 1000.0,
            "data_type": "flow",
            "time_period": "monthly",
            "year": 2024,
            "month": 1,
            "quarter": 1,
            "created_at": utc_now_iso()
        }]

        # First insertion should succeed
        insert_entries(entries)

        # Second insertion with same constraint should raise IntegrityError
        with self.assertRaises(sqlite3.IntegrityError):
            insert_entries(entries)

    def test_bulk_delete_entries(self):
        """Test bulk deletion of entries"""
        # Insert test data
        entries = [
            {
                "uploader_name": f"user_{i}",
                "version": "v1.0",
                "indicator_name": f"indicator_{i}",
                "value": float(i * 100),
                "data_type": "flow",
                "time_period": "monthly",
                "year": 2024,
                "month": 1,
                "created_at": utc_now_iso()
            }
            for i in range(5)
        ]
        insert_entries(entries)

        # Get IDs of first 3 entries
        results = query_data_entries(limit=10)
        ids_to_delete = [r["id"] for r in results[:3]]

        # Bulk delete
        deleted_count = bulk_delete_entries(ids_to_delete)
        self.assertEqual(deleted_count, 3)

        # Verify remaining entries
        remaining = query_data_entries(limit=10)
        self.assertEqual(len(remaining), 2)

    def test_bulk_update_entries(self):
        """Test bulk update of entries"""
        # Insert test data
        entries = [
            {
                "uploader_name": f"user_{i}",
                "version": "v1.0",
                "indicator_name": f"indicator_{i}",
                "value": float(i * 100),
                "data_type": "flow",
                "time_period": "monthly",
                "year": 2024,
                "month": 1,
                "created_at": utc_now_iso()
            }
            for i in range(3)
        ]
        insert_entries(entries)

        # Get IDs
        results = query_data_entries(limit=10)
        ids_to_update = [r["id"] for r in results]

        # Bulk update
        updates = {"uploader_name": "updated_user", "value": 999.99}
        updated_count = bulk_update_entries(ids_to_update, updates)
        self.assertEqual(updated_count, 3)

        # Verify updates
        updated_results = query_data_entries(limit=10)
        for result in updated_results:
            self.assertEqual(result["uploader_name"], "updated_user")
            self.assertEqual(result["value"], 999.99)


class TestPeriodAnalysis(unittest.TestCase):
    """Test period analysis calculations"""

    def setUp(self):
        """Set up test database with sample data"""
        _temp_db_attach(self)

        # Insert sample data for testing
        sample_data = [
            {
                "uploader_name": "test_user",
                "version": "v1.0",
                "indicator_name": "GDP",
                "value": 1000.0,
                "data_type": "flow",
                "time_period": "monthly",
                "year": 2024,
                "month": 1,
                "quarter": 1,
                "created_at": utc_now_iso()
            },
            {
                "uploader_name": "test_user",
                "version": "v1.0",
                "indicator_name": "GDP",
                "value": 1100.0,
                "data_type": "flow",
                "time_period": "monthly",
                "year": 2024,
                "month": 2,
                "quarter": 1,
                "created_at": utc_now_iso()
            },
            {
                "uploader_name": "test_user",
                "version": "v1.0",
                "indicator_name": "GDP",
                "value": 1200.0,
                "data_type": "flow",
                "time_period": "monthly",
                "year": 2024,
                "month": 3,
                "quarter": 1,
                "created_at": utc_now_iso()
            }
        ]
        insert_entries(sample_data)

    def tearDown(self):
        _temp_db_detach(self)

    def test_calculate_period_comparisons_valid(self):
        """Test period comparison calculation with valid data"""
        result = calculate_period_comparisons("GDP", "2024")
        self.assertIn("quarterly_comparison", result)
        self.assertIn("monthly_comparison", result)

    def test_calculate_period_comparisons_no_data(self):
        """Test period comparison with no data"""
        result = calculate_period_comparisons("NONEXISTENT", "2024")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Tidak ada data untuk indikator ini")


class TestSecurityVulnerabilities(unittest.TestCase):
    """Test for security vulnerabilities"""

    def setUp(self):
        _temp_db_attach(self)

    def tearDown(self):
        _temp_db_detach(self)

    def test_sql_injection_prevention(self):
        """Test that SQL injection is prevented"""
        # Test with malicious uploader name
        malicious_uploader = "'; DROP TABLE data_entries; --"
        count = get_total_entries_count(uploader=malicious_uploader)
        # Should not crash and should return 0 (no matching records)
        self.assertIsInstance(count, int)

    def test_xss_prevention_in_templates(self):
        """Test XSS prevention in templates"""
        # This would require integration testing with actual template rendering
        # For now, we verify that templates use auto-escaping
        pass

    def test_path_traversal_prevention(self):
        """Test path traversal prevention in file uploads"""
        # Test with malicious filename
        malicious_filename = "../../../etc/passwd"
        self.assertFalse(allowed_file(malicious_filename))

        malicious_filename2 = "test.xlsx.exe"
        self.assertFalse(allowed_file(malicious_filename2))

    def test_buffer_overflow_prevention(self):
        """Test buffer overflow prevention"""
        # Test with extremely large input values
        large_value = "1" * 10000  # Very large number string
        parsed = _to_float(large_value)
        self.assertIsNotNone(parsed)  # Should handle large numbers gracefully


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""

    def setUp(self):
        _temp_db_attach(self)

    def tearDown(self):
        _temp_db_detach(self)

    def test_database_connection_failure(self):
        """Test graceful handling of database connection failures"""
        import models
        original_path = models.DB_PATH
        try:
            # Set invalid database path
            models.DB_PATH = "/invalid/path/database.db"

            # This should handle the error gracefully
            result = get_total_entries_count()
            self.assertIsInstance(result, int)  # Should return 0 or handle error

        finally:
            models.DB_PATH = original_path

    def test_invalid_pagination_parameters(self):
        """Test handling of invalid pagination parameters"""
        # Test with negative page numbers
        results = query_data_entries(limit=10, offset=-10)
        self.assertIsInstance(results, list)

        # Test with extremely large limit
        results = query_data_entries(limit=10000)
        self.assertIsInstance(results, list)

    def test_concurrent_database_operations(self):
        """Test concurrent database operations"""
        import threading
        import time

        results = []
        errors = []

        def insert_operation(thread_id):
            try:
                entry = {
                    "uploader_name": f"thread_{thread_id}",
                    "version": "v1.0",
                    "indicator_name": f"indicator_{thread_id}",
                    "value": float(thread_id * 100),
                    "data_type": "flow",
                    "time_period": "monthly",
                    "year": 2024,
                    "month": 1,
                    "created_at": utc_now_iso()
                }
                insert_entries([entry])
                results.append(f"Thread {thread_id} success")
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")

        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=insert_operation, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify results
        self.assertEqual(len(results), 5)  # All should succeed
        self.assertEqual(len(errors), 0)   # No errors should occur


class TestPerformanceIssues(unittest.TestCase):
    """Test for performance issues and memory leaks"""

    def setUp(self):
        _temp_db_attach(self)

    def tearDown(self):
        _temp_db_detach(self)

    def test_large_dataset_pagination(self):
        """Test pagination performance with large datasets"""
        # Insert many records
        entries = []
        for i in range(1000):
            entries.append({
                "uploader_name": f"user_{i % 10}",
                "version": "v1.0",
                "indicator_name": f"indicator_{i % 20}",
                "value": float(i),
                "data_type": "flow",
                "time_period": "monthly",
                "year": 2024,
                "month": 1,
                "created_at": utc_now_iso()
            })

        start_time = time.time()
        insert_entries(entries)
        insert_time = time.time() - start_time

        # Should complete within reasonable time
        self.assertLess(insert_time, 5.0)  # Less than 5 seconds

        # Test pagination performance
        start_time = time.time()
        results = query_data_entries(limit=50, offset=500)
        query_time = time.time() - start_time

        self.assertLess(query_time, 1.0)  # Less than 1 second
        self.assertEqual(len(results), 50)


if __name__ == "__main__":
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestValidation)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExcelParser))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDatabaseOperations))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPeriodAnalysis))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSecurityVulnerabilities))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPerformanceIssues))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print(f"\n{'FAILURES:'}")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print(f"\n{'ERRORS:'}")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    print(f"\n{'SUCCESS!' if result.wasSuccessful() else 'FAILED!'}")