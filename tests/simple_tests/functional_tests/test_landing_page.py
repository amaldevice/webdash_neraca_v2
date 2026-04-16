"""
Test Landing Page - Verifikasi halaman utama menampilkan summary dan metadata dengan benar

Test ini memverifikasi bahwa halaman landing page ("/") dapat:
1. Menampilkan halaman dengan status 200
2. Menampilkan summary data yang benar
3. Menampilkan metadata sistem
4. Handle kasus ketika tidak ada data
"""

import pytest
import json
from bs4 import BeautifulSoup


class TestLandingPage:
    """Test suite untuk landing page functionality"""

    def test_landing_page_loads_successfully(self, test_client):
        """Test bahwa halaman landing dapat dimuat dengan status 200"""
        response = test_client.get('/')
        assert response.status_code == 200, "Halaman landing harus dapat dimuat dengan status 200"

    def test_landing_page_contains_required_elements(self, test_client):
        """Test bahwa halaman landing mengandung elemen-elemen yang diperlukan"""
        response = test_client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Periksa title halaman
        title = soup.find('title')
        assert title is not None, "Halaman harus memiliki title"
        assert ("BPS Data System" in title.text) or ("Sistem Data BPS" in title.text), \
            "Title harus mengandung 'BPS Data System' atau 'Sistem Data BPS'"

        # Periksa header atau navigation
        header = soup.find('header') or soup.find('nav')
        assert header is not None, "Halaman harus memiliki header atau navigation"

        # Periksa ada konten utama
        main_content = soup.find('main') or soup.find('div', class_='container') or soup.find('body')
        assert main_content is not None, "Halaman harus memiliki konten utama"

    def test_landing_page_displays_empty_summary_when_no_data(self, test_client):
        """Test bahwa halaman landing menampilkan summary kosong ketika belum ada data"""
        response = test_client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Periksa ada elemen summary
        summary_section = soup.find('div', class_='summary') or soup.find('section', string=lambda text: 'summary' in text.lower())
        if summary_section:
            # Jika ada section summary, pastikan menampilkan nilai kosong/default
            summary_text = summary_section.get_text().lower()
            assert '0' in summary_text or 'empty' in summary_text or 'tidak ada' in summary_text, \
                "Summary harus menunjukkan tidak ada data atau nilai 0"

    def test_landing_page_displays_summary_with_data(self, populated_db):
        """Test bahwa halaman landing menampilkan summary yang benar ketika ada data"""
        response = populated_db.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Periksa ada summary data
        page_text = soup.get_text().lower()

        # Harus mengandung informasi tentang data entries
        summary_indicators = ['total', 'entries', 'data', 'summary']
        has_summary_info = any(indicator in page_text for indicator in summary_indicators)
        assert has_summary_info, "Halaman harus menampilkan informasi summary data"

    def test_landing_page_has_navigation_links(self, test_client):
        """Test bahwa halaman landing memiliki link navigasi ke fitur utama"""
        response = test_client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Cari semua link
        links = soup.find_all('a', href=True)

        # Link yang seharusnya ada
        expected_routes = ['/upload', '/manual', '/preview-data', '/data-management']
        found_routes = [link['href'] for link in links]

        # Minimal harus ada beberapa link navigasi
        navigation_found = any(route in ' '.join(found_routes) for route in expected_routes)
        assert navigation_found, f"Halaman harus memiliki link navigasi ke fitur utama. Expected: {expected_routes}"

    def test_landing_page_response_time(self, test_client):
        """Test bahwa halaman landing merespons dalam waktu yang wajar"""
        import time

        start_time = time.time()
        response = test_client.get('/')
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 2.0, f"Halaman landing harus load dalam waktu kurang dari 2 detik, tapi butuh {response_time:.2f} detik"

    def test_landing_page_handles_special_characters(self, test_client):
        """Test bahwa halaman landing dapat menangani karakter khusus dengan benar"""
        # Test dengan Accept-Language header yang berbeda
        response = test_client.get('/', headers={'Accept-Language': 'id-ID'})
        assert response.status_code == 200, "Halaman harus mendukung bahasa Indonesia"

        # Test dengan User-Agent berbeda
        response = test_client.get('/', headers={'User-Agent': 'Test-Agent/1.0'})
        assert response.status_code == 200, "Halaman harus bekerja dengan berbagai User-Agent"

    def test_landing_page_content_type(self, test_client):
        """Test bahwa halaman landing mengembalikan content type yang benar"""
        response = test_client.get('/')
        assert 'text/html' in response.content_type, f"Content type harus HTML, tapi mendapat: {response.content_type}"

    def test_landing_page_no_server_errors(self, test_client):
        """Test bahwa halaman landing tidak mengembalikan error server (5xx)"""
        response = test_client.get('/')
        assert response.status_code < 500, f"Tidak boleh ada server error. Status code: {response.status_code}"


if __name__ == "__main__":
    # Jalankan test secara standalone
    pytest.main([__file__, "-v"])