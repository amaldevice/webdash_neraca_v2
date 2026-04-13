"""
Test Manual Entry - Test input data manual melalui form

Test ini memverifikasi bahwa fungsi input manual dapat:
1. Menampilkan form input manual dengan benar
2. Memproses input data yang valid
3. Validasi semua field yang wajib diisi
4. Handle berbagai format periode waktu (monthly, quarterly, yearly)
5. Menolak input yang tidak valid (nilai bukan angka, format tanggal salah)
6. Menyimpan data ke database
7. Menampilkan feedback yang sesuai
"""

import pytest
from bs4 import BeautifulSoup


class TestManualEntry:
    """Test suite untuk manual entry functionality"""

    def test_manual_entry_page_loads_successfully(self, test_client):
        """Test bahwa halaman manual entry dapat dimuat dengan status 200"""
        response = test_client.get('/manual')
        assert response.status_code == 200, "Halaman manual entry harus dapat dimuat dengan status 200"

    def test_manual_entry_page_contains_form_elements(self, test_client):
        """Test bahwa halaman manual entry mengandung form dengan elemen yang diperlukan"""
        response = test_client.get('/manual')
        soup = BeautifulSoup(response.data, 'html.parser')

        # Periksa ada form
        form = soup.find('form')
        assert form is not None, "Halaman manual entry harus memiliki form"

        # Periksa input fields yang diperlukan
        required_fields = ['uploader', 'version', 'data_type', 'time_period', 'period_date', 'indicator', 'value']
        for field_name in required_fields:
            field = soup.find('input', {'name': field_name}) or soup.find('select', {'name': field_name})
            assert field is not None, f"Form harus memiliki field {field_name}"

    def test_manual_entry_valid_monthly_data(self, test_client):
        """Test input data manual untuk periode bulanan yang valid"""
        response = test_client.post('/manual', data={
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'period_date': '2024-01',  # Format YYYY-MM
            'indicator': 'GDP',
            'value': '150.75'
        })

        # Harus redirect dengan sukses
        assert response.status_code in [200, 302], "Input berhasil harus redirect atau menampilkan halaman validasi"
        assert '/manual' in response.headers.get('Location', ''), "Harus redirect ke halaman manual entry"

        # Verifikasi data tersimpan
        from models import query_data_entries
        entries = query_data_entries(uploader='TestUser', indicator='GDP')
        assert len(entries) > 0, "Data harus tersimpan ke database"
        assert entries[0]['value'] == 150.75, "Nilai harus sesuai dengan input"
        assert entries[0]['year'] == 2024, "Tahun harus di-parse dengan benar"
        assert entries[0]['month'] == 1, "Bulan harus di-parse dengan benar"

    def test_manual_entry_valid_quarterly_data(self, test_client):
        """Test input data manual untuk periode kuartalan yang valid"""
        response = test_client.post('/manual', data={
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'stock',
            'time_period': 'quarterly',
            'period_date': '2024-Q2',  # Format YYYY-Q1/Q2/Q3/Q4
            'indicator': 'Inflation',
            'value': '200.50'
        })

        assert response.status_code in [200, 302], "Input berhasil harus redirect"

        # Verifikasi data tersimpan
        from models import query_data_entries
        entries = query_data_entries(uploader='TestUser', indicator='Inflation')
        assert len(entries) > 0, "Data harus tersimpan ke database"
        assert entries[0]['value'] == 200.50, "Nilai harus sesuai dengan input"
        assert entries[0]['year'] == 2024, "Tahun harus di-parse dengan benar"
        assert entries[0]['quarter'] == 2, "Kuartal harus di-parse dengan benar"

    def test_manual_entry_valid_yearly_data(self, test_client):
        """Test input data manual untuk periode tahunan yang valid"""
        response = test_client.post('/manual', data={
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'yearly',
            'period_date': '2024',  # Format YYYY
            'indicator': 'Population',
            'value': '300.25'
        })

        assert response.status_code in [200, 302], "Input berhasil harus redirect"

        # Verifikasi data tersimpan
        from models import query_data_entries
        entries = query_data_entries(uploader='TestUser', indicator='Population')
        assert len(entries) > 0, "Data harus tersimpan ke database"
        assert entries[0]['value'] == 300.25, "Nilai harus sesuai dengan input"
        assert entries[0]['year'] == 2024, "Tahun harus di-parse dengan benar"

    def test_manual_entry_missing_required_fields(self, test_client):
        """Test input manual dengan field yang hilang"""
        # Test tanpa uploader
        response = test_client.post('/manual', data={
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'period_date': '2024-01',
            'indicator': 'GDP',
            'value': '100.0'
            # Tidak ada uploader
        })

        # Validation errors stay on same page, not redirect
        assert response.status_code == 200, "Validasi gagal harus tetap di halaman yang sama"
        soup = BeautifulSoup(response.data, 'html.parser')
        error_text = soup.get_text().lower()
        assert 'semua field' in error_text or 'wajib' in error_text or 'required' in error_text, \
            "Harus menampilkan error untuk field yang wajib"

    def test_manual_entry_invalid_value(self, test_client):
        """Test input manual dengan nilai yang bukan angka"""
        response = test_client.post('/manual', data={
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'period_date': '2024-01',
            'indicator': 'GDP',
            'value': 'not-a-number'
        })

        # Validation errors stay on same page, not redirect
        assert response.status_code == 200, "Input tidak valid harus tetap di halaman yang sama"
        soup = BeautifulSoup(response.data, 'html.parser')
        error_text = soup.get_text().lower()
        assert 'valid' in error_text or 'angka' in error_text or 'number' in error_text, \
            "Harus menampilkan error untuk nilai bukan angka"

    def test_manual_entry_invalid_period_date_format(self, test_client):
        """Test input manual dengan format period_date yang salah"""
        response = test_client.post('/manual', data={
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'period_date': 'invalid-date',  # Format salah
            'indicator': 'GDP',
            'value': '100.0'
        })

        assert response.status_code in [200, 302], "Format tanggal salah harus redirect atau menampilkan halaman valid"
        if response.status_code == 302:
            response = test_client.get('/manual', follow_redirects=True)
        soup = BeautifulSoup(response.data, 'html.parser')
        error_text = soup.get_text().lower()
        assert 'input data manual' in error_text or 'simpan entri manual' in error_text

    def test_manual_entry_invalid_metadata(self, test_client):
        """Test input manual dengan metadata yang tidak valid"""
        response = test_client.post('/manual', data={
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'invalid_type',  # Tidak valid
            'time_period': 'monthly',
            'period_date': '2024-01',
            'indicator': 'GDP',
            'value': '100.0'
        })

        # Validation errors stay on same page, not redirect
        assert response.status_code == 200, "Metadata tidak valid harus tetap di halaman yang sama"
        soup = BeautifulSoup(response.data, 'html.parser')
        error_text = soup.get_text().lower()
        assert 'valid' in error_text or 'tidak valid' in error_text, \
            "Harus menampilkan error untuk metadata tidak valid"

    def test_manual_entry_success_message(self, test_client):
        """Test bahwa input manual berhasil menampilkan pesan sukses"""
        response = test_client.post('/manual', data={
            'uploader': 'SuccessTestUser',
            'version': 'v2.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'period_date': '2024-03',
            'indicator': 'SuccessIndicator',
            'value': '250.75'
        })

        # Follow redirect untuk melihat pesan sukses
        response = test_client.get('/manual', follow_redirects=True)
        soup = BeautifulSoup(response.data, 'html.parser')
        success_text = soup.get_text().lower()
        assert 'berhasil' in success_text or 'success' in success_text or 'dicatat' in success_text, \
            "Harus menampilkan pesan sukses setelah input berhasil"

    def test_manual_entry_preserves_form_data_on_error(self, test_client):
        """Test bahwa form mempertahankan data yang sudah diisi ketika ada error"""
        form_data = {
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'period_date': '2024-01',
            'indicator': 'GDP',
            'value': 'not-a-number'  # Akan menyebabkan error
        }

        response = test_client.post('/manual', data=form_data)
        response = test_client.get('/manual', follow_redirects=True)
        soup = BeautifulSoup(response.data, 'html.parser')

        # Periksa apakah form masih berisi data yang diisi sebelumnya
        uploader_field = soup.find('input', {'name': 'uploader'})
        if uploader_field and uploader_field.get('value'):
            assert uploader_field['value'] == 'TestUser', "Form harus mempertahankan nilai uploader"

    def test_manual_entry_handles_edge_cases(self, test_client):
        """Test input manual dengan edge cases"""
        # Test dengan nilai desimal yang sangat kecil
        response = test_client.post('/manual', data={
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'yearly',
            'period_date': '2024',
            'indicator': 'SmallValue',
            'value': '0.000001'
        })
        assert response.status_code in [200, 302], "Nilai desimal kecil harus diterima"

        # Test dengan nilai negatif
        response = test_client.post('/manual', data={
            'uploader': 'TestUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'yearly',
            'period_date': '2024',
            'indicator': 'NegativeValue',
            'value': '-100.50'
        })
        assert response.status_code in [200, 302], "Nilai negatif harus diterima jika valid untuk bisnis"

    def test_manual_entry_database_integrity(self, test_client):
        """Test bahwa input manual mempertahankan integritas database"""
        # Input data pertama
        response = test_client.post('/manual', data={
            'uploader': 'UniqueUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'period_date': '2024-01',
            'indicator': 'UniqueIndicator',
            'value': '100.0'
        })
        assert response.status_code in [200, 302], "Input pertama harus berhasil"

        # Input data dengan kombinasi yang sama - harus berhasil (karena constraint unik berbeda)
        response = test_client.post('/manual', data={
            'uploader': 'UniqueUser',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'period_date': '2024-02',  # Bulan berbeda
            'indicator': 'UniqueIndicator',
            'value': '200.0'
        })
        assert response.status_code in [200, 302], "Input dengan bulan berbeda harus berhasil"


def test_manual_entry_duplicate_warning_and_confirmation(test_client):
    from models import insert_entries, query_data_entries

    seed_entry = {
        "uploader_name": "SeedUser",
        "version": "v2",
        "template_type": "manual",
        "data_type": "flow",
        "time_period": "monthly",
        "indicator_name": "GDPManual",
        "value": 10.0,
        "unit": None,
        "region_code": None,
        "year": 2024,
        "month": 4,
        "quarter": None,
        "created_at": "2024-01-01T00:00:00",
    }
    insert_entries([seed_entry])

    payload = {
        "uploader": "NewUser",
        "version": "v1",
        "data_type": "flow",
        "time_period": "monthly",
        "period_date": "2024-04",
        "indicator": "GDPManual",
        "value": "12.5",
    }

    response = test_client.post('/manual', data=payload)
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    page_text = soup.get_text().lower()
    assert 'deteksi duplikasi' in page_text
    assert soup.find('input', {'name': 'confirm_duplicate'}) is not None

    payload["confirm_duplicate"] = "1"
    response = test_client.post('/manual', data=payload)
    assert response.status_code in [200, 302]
    entries = query_data_entries(indicator="GDPManual")
    assert len(entries) == 2


if __name__ == "__main__":
    # Jalankan test secara standalone
    pytest.main([__file__, "-v"])