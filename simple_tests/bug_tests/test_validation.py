"""
Test Input Validation - BPS Data Management System
Testing untuk validasi input, boundary values, dan injection attacks
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from io import BytesIO
import pandas as pd


class TestInputValidation:
    """Test class untuk input validation"""

    def test_invalid_file_extensions(self, test_client):
        """Test upload dengan ekstensi file yang tidak valid"""
        # Test dengan berbagai ekstensi yang tidak valid
        invalid_files = [
            ("test.txt", b"text content", "text/plain"),
            ("test.pdf", b"pdf content", "application/pdf"),
            ("test.exe", b"exe content", "application/octet-stream"),
            ("test.zip", b"zip content", "application/zip"),
        ]

        for filename, content, mimetype in invalid_files:
            data = {
                'uploader': 'TestUser',
                'version': 'v1.0',
                'data_type': 'flow',
                'time_period': 'monthly'
            }
            file_data = (BytesIO(content), filename)

            response = test_client.post('/upload',
                                     data={**data, 'excel_file': file_data})

            # Should either redirect (302) or return error page (200 with error)
            assert response.status_code in [200, 302]

            if response.status_code == 302:
                # Check for flash messages
                with test_client.session_transaction() as sess:
                    flashed_messages = sess.get('_flashes', [])
                    assert len(flashed_messages) > 0
                    error_found = any("Excel" in msg[1] for msg in flashed_messages)
                    assert error_found, f"Expected Excel error for {filename}, got: {flashed_messages}"
            else:
                # Check response content for error
                response_text = response.get_data(as_text=True)
                assert "error" in response_text.lower() or "tidak valid" in response_text

    def test_empty_required_fields(self, test_client):
        """Test upload dengan field yang wajib kosong"""
        test_cases = [
            ("uploader", "", "Nama pengupload wajib diisi."),
            ("version", "", "Versioning wajib diisi."),
        ]

        for field_name, field_value, expected_error in test_cases:
                # Create a minimal valid Excel file
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': 'TestUser' if field_name != 'uploader' else field_value,
                    'version': 'v1.0' if field_name != 'version' else field_value,
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                assert response.status_code == 302
                with client.session_transaction() as sess:
                    flashed_messages = sess.get('_flashes', [])
                    assert len(flashed_messages) > 0
                    error_found = any(expected_error in msg[1] for msg in flashed_messages)
                    assert error_found, f"Expected error '{expected_error}' for empty {field_name}"

    def test_invalid_data_type_values(self, test_client):
        """Test dengan nilai data_type yang tidak valid"""
        invalid_data_types = ["invalid", "FLOW", "STOCK", "123", "", " ", "flow stock"]

        for invalid_type in invalid_data_types:
            df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)

            data = {
                'uploader': 'TestUser',
                'version': 'v1.0',
                'data_type': invalid_type,
                'time_period': 'monthly'
            }
            file_data = (excel_buffer, 'test.xlsx')

            response = test_client.post('/upload',
                                     data={**data, 'excel_file': file_data})

            assert response.status_code == 302
            with test_client.session_transaction() as sess:
                flashed_messages = sess.get('_flashes', [])
                assert len(flashed_messages) > 0
                error_found = any("Tipe data tidak valid" in msg[1] for msg in flashed_messages)
                assert error_found, f"Expected validation error for data_type '{invalid_type}'"

    def test_invalid_time_period_values(self, test_client):
        """Test dengan nilai time_period yang tidak valid"""
        invalid_periods = ["invalid", "MONTHLY", "YEARLY", "123", "", " ", "monthly yearly"]

        for invalid_period in invalid_periods:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': 'TestUser',
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': invalid_period
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                assert response.status_code == 302
                with client.session_transaction() as sess:
                    flashed_messages = sess.get('_flashes', [])
                    assert len(flashed_messages) > 0
                    error_found = any("Periode tidak valid" in msg[1] for msg in flashed_messages)
                    assert error_found, f"Expected validation error for time_period '{invalid_period}'"

    def test_boundary_value_file_size(self, test_client):
        """Test dengan file yang mendekati batas ukuran maksimum"""
        # Create file close to 16MB limit
        large_content = b"x" * (15 * 1024 * 1024)  # 15MB

        with test_client as client:
            data = {
                'uploader': 'TestUser',
                'version': 'v1.0',
                'data_type': 'flow',
                'time_period': 'monthly'
            }
            file_data = (BytesIO(large_content), 'large_test.xlsx')

            response = client.post('/upload',
                                 data=data,
                                 content_type='multipart/form-data',
                                 data_file=file_data)

            # Should still work as it's under the limit
            assert response.status_code == 302

    def test_malformed_excel_files(self, test_client):
        """Test dengan file Excel yang malformed atau korup"""
        malformed_contents = [
            b"PK\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",  # Partial ZIP header
            b"<html><body>Malformed Excel</body></html>",  # HTML content
            b"",  # Empty file
            b"\x00\x01\x02\x03\x04\x05",  # Random bytes
        ]

        for malformed_content in malformed_contents:
            with test_client as client:
                data = {
                    'uploader': 'TestUser',
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (BytesIO(malformed_content), 'malformed.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                assert response.status_code == 302
                with client.session_transaction() as sess:
                    flashed_messages = sess.get('_flashes', [])
                    # Should either fail validation or parsing
                    assert len(flashed_messages) > 0

    def test_extremely_long_field_values(self, test_client):
        """Test dengan nilai field yang sangat panjang"""
        long_value = "A" * 10000  # 10KB string

        with test_client as client:
            df = pd.DataFrame({'Indicator': [long_value], '2024-01': [100]})
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)

            data = {
                'uploader': long_value,
                'version': long_value,
                'data_type': 'flow',
                'time_period': 'monthly'
            }
            file_data = (excel_buffer, 'test.xlsx')

            response = client.post('/upload',
                                 data=data,
                                 content_type='multipart/form-data',
                                 data_file=file_data)

            # Should handle gracefully (either succeed or fail with appropriate error)
            assert response.status_code in [200, 302]

    def test_special_characters_in_fields(self, test_client):
        """Test dengan karakter spesial dalam field"""
        special_chars = [
            "Test<User>", "Test'User", 'Test"User', "Test\\User",
            "Test/User", "Test:User", "Test*User", "Test?User",
            "Test|User", "Test<User>", "Test\nUser", "Test\tUser"
        ]

        for special_char in special_chars:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': special_char,
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                # Should handle special characters gracefully
                assert response.status_code in [200, 302]

    def test_sql_injection_attempts_in_form_fields(self, test_client):
        """Test SQL injection attempts dalam form fields"""
        sql_injections = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "'; SELECT * FROM users; --",
            "' UNION SELECT password FROM users; --"
        ]

        for sql_payload in sql_injections:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': sql_payload,
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                # Should not crash and should handle the input safely
                assert response.status_code in [200, 302]

    def test_xss_attempts_in_form_fields(self, test_client):
        """Test XSS attempts dalam form fields"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'>",
            "<svg onload=alert('XSS')>"
        ]

        for xss_payload in xss_payloads:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': xss_payload,
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                # Should handle XSS attempts safely
                assert response.status_code in [200, 302]

    def test_numeric_value_validation(self, test_client):
        """Test validasi nilai numerik dalam Excel"""
        # Test dengan berbagai nilai yang tidak valid
        invalid_values = [
            "not_a_number",
            "NaN",
            "Infinity",
            "-Infinity",
            "",
            " ",
            None,
            "1,234.56",  # Comma as decimal separator (might be invalid)
        ]

        for invalid_value in invalid_values:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [invalid_value]})
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

                # Should handle invalid numeric values gracefully
                assert response.status_code in [200, 302]

    def test_boundary_numeric_values(self, test_client):
        """Test dengan nilai numerik ekstrim"""
        boundary_values = [
            0,
            0.000001,
            999999999,
            -999999999,
            float('inf'),
            float('-inf'),
            float('nan')
        ]

        for boundary_value in boundary_values:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [boundary_value]})
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

                # Should handle boundary values
                assert response.status_code in [200, 302]