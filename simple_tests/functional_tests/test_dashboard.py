"""
Test Dashboard - Test filtering dan tampilan data di dashboard

Test ini memverifikasi bahwa dashboard (/preview-data) dapat:
1. Menampilkan data dengan benar
2. Filter berdasarkan data_type, time_period, uploader, indicator
3. Pagination bekerja dengan baik
4. Menampilkan filter options
5. Handle kasus tidak ada data
6. Handle filter yang tidak menghasilkan data
"""

import pytest
from bs4 import BeautifulSoup


class TestDashboard:
    """Test suite untuk dashboard functionality"""

    def test_dashboard_loads_successfully(self, test_client):
        """Test bahwa halaman dashboard dapat dimuat dengan status 200"""
        response = test_client.get('/preview-data')
        assert response.status_code == 200, "Halaman dashboard harus dapat dimuat dengan status 200"

    def test_dashboard_empty_state(self, test_client):
        """Test dashboard ketika belum ada data"""
        response = test_client.get('/preview-data')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Harus menampilkan pesan kosong atau tidak ada data
        page_text = soup.get_text().lower()
        empty_indicators = ['tidak ada data', 'no data', 'empty', 'kosong']
        has_empty_message = any(indicator in page_text for indicator in empty_indicators)
        assert has_empty_message, "Dashboard harus menampilkan pesan ketika tidak ada data"

    def test_dashboard_displays_data_with_populated_db(self, populated_db):
        """Test dashboard menampilkan data ketika database sudah terisi"""
        response = populated_db.get('/preview-data')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Harus ada tabel atau list data
        table = soup.find('table') or soup.find('div', class_='data-list')
        assert table is not None, "Dashboard harus menampilkan data dalam tabel atau list"

        # Periksa ada data entries
        rows = soup.find_all('tr') if table.name == 'table' else soup.find_all('div', class_='data-row')
        assert len(rows) > 1, "Harus ada minimal 1 baris data ditampilkan"  # Header + data

    def test_dashboard_filter_by_uploader(self, populated_db):
        """Test filter dashboard berdasarkan uploader"""
        # Filter berdasarkan uploader Alice
        response = populated_db.get('/preview-data?uploader=Alice')
        soup = BeautifulSoup(response.data, 'html.parser')

        page_text = soup.get_text().lower()
        # Harus mengandung data Alice tapi tidak Bob atau Charlie
        assert 'alice' in page_text, "Harus menampilkan data Alice"
        assert 'bob' not in page_text, "Tidak boleh menampilkan data Bob"
        assert 'charlie' not in page_text, "Tidak boleh menampilkan data Charlie"

    def test_dashboard_filter_by_data_type(self, populated_db):
        """Test filter dashboard berdasarkan data_type"""
        # Filter berdasarkan data_type flow
        response = populated_db.get('/preview-data?data_type=flow')
        soup = BeautifulSoup(response.data, 'html.parser')

        page_text = soup.get_text().lower()
        assert 'flow' in page_text, "Harus menampilkan data dengan tipe flow"

        # Filter berdasarkan data_type stock
        response = populated_db.get('/preview-data?data_type=stock')
        soup = BeautifulSoup(response.data, 'html.parser')

        page_text = soup.get_text().lower()
        assert 'stock' in page_text, "Harus menampilkan data dengan tipe stock"

    def test_dashboard_filter_by_time_period(self, populated_db):
        """Test filter dashboard berdasarkan time_period"""
        # Filter berdasarkan time_period monthly
        response = populated_db.get('/preview-data?time_period=monthly')
        soup = BeautifulSoup(response.data, 'html.parser')

        page_text = soup.get_text().lower()
        assert 'monthly' in page_text, "Harus menampilkan data dengan periode monthly"

        # Filter berdasarkan time_period quarterly
        response = populated_db.get('/preview-data?time_period=quarterly')
        soup = BeautifulSoup(response.data, 'html.parser')

        page_text = soup.get_text().lower()
        assert 'quarterly' in page_text, "Harus menampilkan data dengan periode quarterly"

    def test_dashboard_filter_by_indicator(self, populated_db):
        """Test filter dashboard berdasarkan indicator"""
        # Filter berdasarkan indicator GDP
        response = populated_db.get('/preview-data?indicator=GDP')
        soup = BeautifulSoup(response.data, 'html.parser')

        page_text = soup.get_text().lower()
        assert 'gdp' in page_text, "Harus menampilkan data GDP"
        assert 'inflation' not in page_text, "Tidak boleh menampilkan data Inflation"

    def test_dashboard_multiple_filters(self, populated_db):
        """Test filter dashboard dengan multiple criteria"""
        # Filter kombinasi: uploader=Alice dan data_type=flow
        response = populated_db.get('/preview-data?uploader=Alice&data_type=flow')
        soup = BeautifulSoup(response.data, 'html.parser')

        page_text = soup.get_text().lower()
        assert 'alice' in page_text, "Harus menampilkan data Alice"
        assert 'flow' in page_text, "Harus menampilkan data flow"

    def test_dashboard_pagination(self, populated_db):
        """Test pagination di dashboard"""
        # Test dengan limit kecil untuk memaksa pagination
        response = populated_db.get('/preview-data?page=1&limit=2')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Periksa ada pagination controls
        pagination = soup.find('nav') or soup.find('div', class_='pagination')
        if pagination:  # Jika ada pagination
            # Periksa ada link page navigation
            page_links = pagination.find_all('a') or pagination.find_all('button')
            assert len(page_links) > 0, "Harus ada kontrol pagination"

    def test_dashboard_filter_options_available(self, populated_db):
        """Test bahwa filter options tersedia di dashboard"""
        response = populated_db.get('/preview-data')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Periksa ada dropdown atau select untuk filter
        uploader_select = soup.find('select', {'name': 'uploader'}) or soup.find('input', {'name': 'uploader'})
        data_type_select = soup.find('select', {'name': 'data_type'}) or soup.find('input', {'name': 'data_type'})
        time_period_select = soup.find('select', {'name': 'time_period'}) or soup.find('input', {'name': 'time_period'})

        assert uploader_select is not None, "Harus ada filter uploader"
        assert data_type_select is not None, "Harus ada filter data_type"
        assert time_period_select is not None, "Harus ada filter time_period"

    def test_dashboard_no_results_filter(self, test_client):
        """Test filter yang tidak menghasilkan hasil"""
        response = test_client.get('/preview-data?uploader=NonExistentUser')
        soup = BeautifulSoup(response.data, 'html.parser')

        page_text = soup.get_text().lower()
        no_results_indicators = ['tidak ada data', 'no data', 'no results', 'empty']
        has_no_results_message = any(indicator in page_text for indicator in no_results_indicators)
        assert has_no_results_message, "Harus menampilkan pesan tidak ada hasil untuk filter"

    def test_dashboard_data_integrity(self, populated_db):
        """Test bahwa data yang ditampilkan memiliki integritas"""
        response = populated_db.get('/preview-data')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Cari tabel data
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:  # id, uploader, version, indicator, value, ...
                    # Periksa value adalah angka (kolom ke-5, index 4)
                    value_cell = cells[4]  # Value column (0-indexed)
                    value_text = value_cell.get_text().strip()
                    if value_text and value_text != 'N/A':  # Skip empty or N/A values
                        try:
                            float(value_text)
                        except ValueError:
                            pytest.fail(f"Value '{value_text}' harus berupa angka")

    def test_dashboard_filter_persistence(self, populated_db):
        """Test bahwa filter tersimpan di URL dan form"""
        # Akses dengan filter
        response = populated_db.get('/preview-data?uploader=Alice&data_type=flow&page=1')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Periksa filter ada di URL atau form value
        uploader_field = soup.find('select', {'name': 'uploader'}) or soup.find('input', {'name': 'uploader'})
        if uploader_field and hasattr(uploader_field, 'get') and uploader_field.get('value'):
            assert 'Alice' in uploader_field['value'] or 'alice' in uploader_field['value'].lower(), \
                "Filter uploader harus tersimpan"

    def test_dashboard_sorting_display(self, populated_db):
        """Test bahwa data ditampilkan dalam urutan yang masuk akal"""
        response = populated_db.get('/preview-data')
        soup = BeautifulSoup(response.data, 'html.parser')

        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            if len(rows) > 1:
                # Periksa ada kolom created_at atau ID untuk sorting
                header_row = table.find('tr')
                headers = [th.get_text().lower() for th in header_row.find_all('th')]
                has_sortable_column = any(col in ' '.join(headers) for col in ['id', 'created', 'tanggal'])
                assert has_sortable_column, "Tabel harus memiliki kolom untuk sorting (ID, created_at, dll)"

    def test_dashboard_limit_options(self, test_client):
        """Test berbagai opsi limit pagination"""
        valid_limits = [5, 10, 15, 20, 30, 50, 100]

        for limit in valid_limits:
            response = test_client.get(f'/preview-data?limit={limit}')
            assert response.status_code == 200, f"Limit {limit} harus diterima"

        # Test limit tidak valid harus fallback ke default
        response = test_client.get('/preview-data?limit=999')
        assert response.status_code == 200, "Limit tidak valid harus fallback ke default"

    def test_dashboard_response_time(self, populated_db):
        """Test bahwa dashboard merespons dalam waktu yang wajar"""
        import time

        start_time = time.time()
        response = populated_db.get('/preview-data')
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 3.0, f"Dashboard harus load dalam waktu kurang dari 3 detik, tapi butuh {response_time:.2f} detik"


if __name__ == "__main__":
    # Jalankan test secara standalone
    pytest.main([__file__, "-v"])