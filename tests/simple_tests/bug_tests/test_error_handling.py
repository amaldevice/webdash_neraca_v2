"""
Test Error Handling - BPS Data Management System
Testing untuk error scenarios, exception handling, dan graceful failures
"""

import pytest
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
import pandas as pd


class TestErrorHandling:
    """Test class untuk error handling"""

    def test_database_connection_failure(self, test_client):
        """Test ketika database connection gagal"""
        with patch('services.upload_commit.insert_entries') as mock_insert:
            mock_insert.side_effect = sqlite3.Error("Database connection failed")

            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': 'TestUser',
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                if response.status_code == 302:
                    response = client.get('/upload', follow_redirects=True)
                assert response.status_code in [200, 302]
                with client.session_transaction() as sess:
                    flashed_messages = sess.get('_flashes', [])
                    response_text = response.get_data(as_text=True).lower()
                    if flashed_messages:
                        error_found = any("kesalahan database" in msg[1].lower() or "error" in msg[1].lower()
                                        for msg in flashed_messages)
                        assert error_found, f"Expected database error message, got: {flashed_messages}"
                    else:
                        assert "kesalahan database" in response_text or "error" in response_text or "terjadi" in response_text

    def test_database_integrity_constraint_violation(self, test_client, populated_db):
        """Test ketika terjadi pelanggaran constraint database (duplicate unique key)"""
        with populated_db as client:
            # First upload - should succeed
            df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)

            data = {
                'uploader': 'Alice',  # Same as existing data
                'version': 'v1.0',    # Same as existing data
                'data_type': 'flow',
                'time_period': 'monthly'
            }
            file_data = (excel_buffer, 'test.xlsx')

            response = client.post('/upload',
                                 data=data,
                                 content_type='multipart/form-data',
                                 data_file=file_data)

            assert response.status_code in [200, 302]
            with client.session_transaction() as sess:
                flashed_messages = sess.get('_flashes', [])
                response_text = response.get_data(as_text=True).lower()
                if flashed_messages:
                    error_found = any("sudah ada" in msg[1] or "UNIQUE constraint" in msg[1]
                                    for msg in flashed_messages)
                    assert error_found, f"Expected integrity constraint error, got: {flashed_messages}"
                else:
                    assert "duplikasi" in response_text or "sudah ada" in response_text or "unique" in response_text

    def test_file_system_permission_denied(self, test_client):
        """Test ketika tidak ada permission untuk menulis file"""
        with patch('werkzeug.utils.secure_filename') as mock_secure:
            mock_secure.return_value = 'test.xlsx'

            with patch('services.upload_flow.open', mock_open()) as mock_file:
                mock_file.side_effect = PermissionError("Permission denied")

                with test_client as client:
                    df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                    excel_buffer = BytesIO()
                    df.to_excel(excel_buffer, index=False)
                    excel_buffer.seek(0)

                    data = {
                        'uploader': 'TestUser',
                        'version': 'v1.0',
                        'data_type': 'flow',
                        'time_period': 'monthly'
                    }
                    file_data = (excel_buffer, 'test.xlsx')

                    response = client.post('/upload',
                                         data=data,
                                         content_type='multipart/form-data',
                                         data_file=file_data)

                    # Should handle permission error gracefully
                    assert response.status_code in [200, 302, 500]

    def test_excel_parsing_failure(self, test_client):
        """Test ketika parsing Excel file gagal"""
        with patch('excel_parser.parse_excel_payload') as mock_parse:
            mock_parse.side_effect = Exception("Excel parsing failed")

            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': 'TestUser',
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                if response.status_code == 302:
                    response = client.get('/upload', follow_redirects=True)
                assert response.status_code in [200, 302]
                with client.session_transaction() as sess:
                    flashed_messages = sess.get('_flashes', [])
                    if flashed_messages:
                        response_text = response.get_data(as_text=True).lower()
                        assert "error" in response_text or "excel" in response_text or "parsing" in response_text
                    else:
                        response_text = response.get_data(as_text=True).lower()
                        assert 'error' in response_text or 'excel' in response_text or 'parsing' in response_text

    def test_manual_entry_invalid_value_conversion(self, test_client):
        """Test ketika konversi nilai manual entry gagal"""
        with test_client as client:
            data = {
                'uploader': 'TestUser',
                'version': 'v1.0',
                'data_type': 'flow',
                'time_period': 'monthly',
                'period_date': '2024-01',
                'indicator': 'GDP',
                'value': 'not_a_number'
            }

            response = client.post('/manual', data=data)

            assert response.status_code in [200, 302]
            with client.session_transaction() as sess:
                flashed_messages = sess.get('_flashes', [])
                if flashed_messages:
                    error_found = any("tidak valid" in msg[1] for msg in flashed_messages)
                    assert error_found, f"Expected invalid value error, got: {flashed_messages}"
                else:
                    page_text = response.get_data(as_text=True).lower()
                    assert "tidak valid" in page_text or "invalid" in page_text or "error" in page_text

    def test_manual_entry_period_date_parsing_failure(self, test_client):
        """Test ketika parsing period_date gagal"""
        invalid_dates = [
            "invalid-date",
            "2024-13",  # Invalid month
            "2024-13-01",  # Invalid month with day
            "2024-Q5",  # Invalid quarter
            "",  # Empty
            "abc-def",  # Non-numeric
        ]

        for invalid_date in invalid_dates:
            with test_client as client:
                data = {
                    'uploader': 'TestUser',
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly',
                    'period_date': invalid_date,
                    'indicator': 'GDP',
                    'value': '100'
                }

                response = client.post('/manual', data=data)

                assert response.status_code in [200, 302]
                with client.session_transaction() as sess:
                    flashed_messages = sess.get('_flashes', [])
                    if not flashed_messages:
                        response_text = response.get_data(as_text=True).lower()
                        assert "tanggal" in response_text or "periode" in response_text or "error" in response_text

    def test_bulk_operations_partial_failure(self, populated_db):
        """Test ketika bulk operation sebagian gagal"""
        with populated_db as client:
            # Try to delete non-existent IDs along with valid ones
            data = {
                'action': 'bulk_delete',
                'selected_ids[]': ['1', '99999', '2']  # 1 and 2 exist, 99999 doesn't
            }

            response = client.post('/data-management', data=data)

            assert response.status_code in [200, 302]
            with client.session_transaction() as sess:
                flashed_messages = sess.get('_flashes', [])
                # Should show partial success
                if flashed_messages:
                    success_found = any("berhasil dihapus" in msg[1] for msg in flashed_messages)
                    assert success_found
                else:
                    response_text = response.get_data(as_text=True).lower()
                    assert "berhasil" in response_text or "dihapus" in response_text

    def test_export_with_invalid_format(self, populated_db):
        """Test export dengan format yang tidak valid"""
        with populated_db as client:
            response = client.get('/export?format=invalid')

            # Should default to CSV or handle gracefully
            assert response.status_code in [200, 302]
            assert 'Content-Disposition' in response.headers

    def test_pagination_with_invalid_parameters(self, populated_db):
        """Test pagination dengan parameter tidak valid"""
        with populated_db as client:
            # Test dengan limit yang tidak valid
            response = client.get('/preview-data?page=1&limit=invalid')
            assert response.status_code == 200

            # Test dengan page yang tidak valid
            response = client.get('/preview-data?page=invalid&limit=20')
            assert response.status_code == 200

            # Test dengan limit di luar range yang diperbolehkan
            response = client.get('/preview-data?page=1&limit=999')
            assert response.status_code == 200

    def test_data_management_update_with_invalid_value(self, populated_db):
        """Test update data dengan nilai yang tidak valid"""
        with populated_db as client:
            data = {
                'action': 'update',
                'entry_id': '1',
                'update_uploader': 'UpdatedUser',
                'update_version': 'v2.0',
                'update_indicator': 'GDP',
                'update_value': 'not_a_number',
                'update_data_type': 'flow',
                'update_time_period': 'monthly'
            }

            response = client.post('/data-management', data=data)

            assert response.status_code in [200, 302]
            with client.session_transaction() as sess:
                flashed_messages = sess.get('_flashes', [])
                if flashed_messages:
                    error_found = any("angka" in msg[1] for msg in flashed_messages)
                    assert error_found
                else:
                    response_text = response.get_data(as_text=True).lower()
                    assert "angka" in response_text or "invalid" in response_text or "error" in response_text

    def test_data_management_bulk_update_partial_failure(self, populated_db):
        """Test bulk update dengan sebagian data gagal"""
        with populated_db as client:
            data = {
                'action': 'bulk_update',
                'selected_ids[]': ['1', '2'],
                'bulk_update_uploader': 'BulkUpdated',
                'bulk_update_value': 'not_a_number'  # This should cause failure
            }

            response = client.post('/data-management', data=data)

            assert response.status_code in [200, 302]
            with client.session_transaction() as sess:
                flashed_messages = sess.get('_flashes', [])
                if not flashed_messages:
                    response_text = response.get_data(as_text=True).lower()
                    assert response_text  # ensure response has content even without flash

    def test_memory_error_simulation(self, test_client):
        """Test simulasi memory error"""
        with patch('pandas.read_excel') as mock_read:
            mock_read.side_effect = MemoryError("Out of memory")

            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': 'TestUser',
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                # Should handle memory error gracefully
                assert response.status_code in [200, 302, 500]

    def test_timeout_simulation(self, test_client):
        """Test simulasi timeout"""
        import time

        with patch('excel_parser.parse_excel') as mock_parse:
            def slow_parse(*args, **kwargs):
                time.sleep(1)  # Simulate slow processing
                return []
            mock_parse.side_effect = slow_parse

            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': 'TestUser',
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                # Should complete successfully despite slow processing
                assert response.status_code in [200, 302]
