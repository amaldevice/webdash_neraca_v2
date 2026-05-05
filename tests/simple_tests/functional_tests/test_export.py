"""
Test Export - Test export data ke CSV dan Excel

Test ini memverifikasi bahwa fungsi export dapat:
1. Export data ke format CSV dengan benar
2. Export data ke format Excel dengan benar
3. Filter data selama export
4. Menampilkan headers yang tepat
5. Handle kasus tidak ada data
6. Validasi isi file yang di-export
"""

import pytest
import csv
import io
import pandas as pd


class TestExport:
    """Test suite untuk export functionality"""

    def test_export_csv_empty_database(self, test_client):
        """Test export CSV ketika database kosong"""
        response = test_client.get('/export?format=csv')

        assert response.status_code == 200, "Export CSV harus berhasil meski kosong"
        assert 'text/csv' in response.content_type, "Content type harus CSV"
        assert 'attachment; filename=raw-data.csv' in response.headers.get('Content-Disposition', '')

        # Parse CSV content
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # Minimal harus ada header
        assert len(rows) >= 1, "CSV harus minimal memiliki header"
        expected_headers = ['id', 'uploader_name', 'version', 'indicator_name', 'value', 'data_type', 'time_period', 'created_at']
        assert rows[0] == expected_headers, f"Header CSV harus {expected_headers}"

    def test_export_excel_empty_database(self, test_client):
        """Test export Excel ketika database kosong"""
        response = test_client.get('/export?format=excel')

        assert response.status_code == 200, "Export Excel harus berhasil meski kosong"
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.content_type
        assert 'attachment; filename=raw-data.xlsx' in response.headers.get('Content-Disposition', '')

        # Verifikasi bisa parse sebagai Excel
        try:
            df = pd.read_excel(io.BytesIO(response.data))
            assert len(df.columns) > 0, "Excel harus memiliki kolom header"
        except Exception as e:
            pytest.fail(f"File Excel tidak valid: {e}")

    def test_export_csv_with_data(self, populated_db):
        """Test export CSV dengan data"""
        response = populated_db.get('/export?format=csv')

        assert response.status_code == 200, "Export CSV harus berhasil"
        assert 'text/csv' in response.content_type, "Content type harus CSV"

        # Parse dan validasi CSV
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # Harus ada header + data
        assert len(rows) > 1, "CSV harus memiliki header dan data"

        # Validasi header
        expected_headers = ['id', 'uploader_name', 'version', 'indicator_name', 'value', 'data_type', 'time_period', 'created_at']
        assert rows[0] == expected_headers, f"Header CSV harus {expected_headers}"

        # Validasi data rows
        for row in rows[1:]:  # Skip header
            assert len(row) == len(expected_headers), "Jumlah kolom harus sesuai header"
            # ID harus integer
            assert row[0].isdigit(), "ID harus berupa angka"
            # Value harus numeric
            try:
                float(row[4])  # value column
            except ValueError:
                pytest.fail(f"Value '{row[4]}' harus berupa angka")

    def test_export_excel_with_data(self, populated_db):
        """Test export Excel dengan data"""
        response = populated_db.get('/export?format=excel')

        assert response.status_code == 200, "Export Excel harus berhasil"
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.content_type

        # Parse dan validasi Excel
        df = pd.read_excel(io.BytesIO(response.data))

        # Harus ada data
        assert len(df) > 0, "Excel harus mengandung data"

        # Validasi kolom yang diperlukan
        required_columns = ['id', 'uploader_name', 'version', 'indicator_name', 'value', 'data_type', 'time_period', 'created_at']
        for col in required_columns:
            assert col in df.columns, f"Kolom {col} harus ada di Excel"

        # Validasi tipe data
        assert df['id'].dtype in ['int64', 'object'], "Kolom ID harus integer"
        assert df['value'].dtype in ['float64', 'int64'], "Kolom value harus numeric"

    def test_export_csv_filtered_by_uploader(self, populated_db):
        """Test export CSV dengan filter uploader"""
        response = populated_db.get('/export?format=csv&uploader=Alice')

        assert response.status_code == 200, "Export CSV dengan filter harus berhasil"

        # Parse CSV
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # Skip header dan validasi hanya ada data Alice
        data_rows = rows[1:]
        for row in data_rows:
            uploader_name = row[1]  # uploader_name column
            assert uploader_name == 'Alice', f"Filter uploader gagal, menemukan {uploader_name}"

    def test_export_excel_filtered_by_data_type(self, populated_db):
        """Test export Excel dengan filter data_type"""
        response = populated_db.get('/export?format=excel&data_type=flow')

        assert response.status_code == 200, "Export Excel dengan filter harus berhasil"

        # Parse Excel
        df = pd.read_excel(io.BytesIO(response.data))

        # Validasi hanya ada data_type flow
        unique_data_types = df['data_type'].unique()
        assert len(unique_data_types) == 1, "Filter data_type harus menghasilkan satu tipe data"
        assert unique_data_types[0] == 'flow', "Filter harus menghasilkan data_type flow"

    def test_export_csv_filtered_by_indicator(self, populated_db):
        """Test export CSV dengan filter indicator"""
        response = populated_db.get('/export?format=csv&indicator=GDP')

        assert response.status_code == 200, "Export CSV dengan filter indicator harus berhasil"

        # Parse CSV
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # Skip header dan validasi hanya ada indicator GDP
        data_rows = rows[1:]
        for row in data_rows:
            indicator = row[3]  # indicator_name column
            assert indicator == 'GDP', f"Filter indicator gagal, menemukan {indicator}"

    def test_export_multiple_filters(self, populated_db):
        """Test export dengan multiple filters"""
        response = populated_db.get('/export?format=csv&uploader=Alice&data_type=flow')

        assert response.status_code == 200, "Export dengan multiple filters harus berhasil"

        # Parse CSV
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # Validasi multiple filters
        data_rows = rows[1:]
        for row in data_rows:
            uploader = row[1]
            data_type = row[5]
            assert uploader == 'Alice', f"Filter uploader gagal, menemukan {uploader}"
            assert data_type == 'flow', f"Filter data_type gagal, menemukan {data_type}"

    def test_export_default_format_is_csv(self, populated_db):
        """Test bahwa format default adalah CSV"""
        response = populated_db.get('/export')  # Tanpa parameter format

        assert response.status_code == 200, "Export default harus berhasil"
        assert 'text/csv' in response.content_type, "Format default harus CSV"

    def test_export_invalid_format_defaults_to_csv(self, populated_db):
        """Test bahwa format tidak valid akan default ke CSV"""
        response = populated_db.get('/export?format=invalid')

        assert response.status_code == 200, "Format tidak valid harus default ke CSV"
        assert 'text/csv' in response.content_type, "Harus fallback ke CSV"

    def test_export_no_data_filtered_result(self, test_client):
        """Test export ketika filter tidak menghasilkan data"""
        response = test_client.get('/export?format=csv&uploader=NonExistentUser')

        assert response.status_code == 200, "Export dengan filter kosong harus berhasil"

        # Parse CSV
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # Harus hanya ada header, tidak ada data
        assert len(rows) == 1, "Filter yang tidak cocok harus menghasilkan hanya header"
        expected_headers = ['id', 'uploader_name', 'version', 'indicator_name', 'value', 'data_type', 'time_period', 'created_at']
        assert rows[0] == expected_headers, f"Header harus tetap ada: {expected_headers}"

    def test_export_csv_data_integrity(self, populated_db):
        """Test integritas data dalam export CSV"""
        # Dapatkan data langsung dari database
        from models import query_data_entries
        db_entries = query_data_entries(limit=1000)

        # Export CSV
        response = populated_db.get('/export?format=csv')
        csv_content = response.data.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        csv_rows = list(csv_reader)

        # Validasi jumlah data
        assert len(csv_rows) == len(db_entries) + 1, "Jumlah baris CSV harus sama dengan database + header"

        # Validasi beberapa sample data
        if len(db_entries) > 0:
            # Ambil entry pertama dari database
            db_entry = db_entries[0]
            # Cari di CSV (skip header)
            csv_data_row = None
            for row in csv_rows[1:]:
                if row[0] == str(db_entry['id']):  # Match by ID
                    csv_data_row = row
                    break

            assert csv_data_row is not None, "Data dari database harus ada di CSV"
            assert csv_data_row[1] == db_entry['uploader_name'], "Uploader name harus sama"
            assert csv_data_row[3] == db_entry['indicator_name'], "Indicator name harus sama"
            assert abs(float(csv_data_row[4]) - db_entry['value']) < 0.001, "Value harus sama"

    def test_export_excel_data_integrity(self, populated_db):
        """Test integritas data dalam export Excel"""
        # Dapatkan data langsung dari database
        from models import query_data_entries
        db_entries = query_data_entries(limit=1000)

        # Export Excel
        response = populated_db.get('/export?format=excel')
        df = pd.read_excel(io.BytesIO(response.data))

        # Validasi jumlah data
        assert len(df) == len(db_entries), "Jumlah baris Excel harus sama dengan database"

        # Validasi beberapa sample data
        if len(db_entries) > 0:
            db_entry = db_entries[0]
            # Cari matching row di Excel
            matching_row = df[df['id'] == db_entry['id']]

            assert len(matching_row) == 1, "Harus ada satu baris yang match di Excel"
            row = matching_row.iloc[0]
            assert row['uploader_name'] == db_entry['uploader_name'], "Uploader name harus sama"
            assert row['indicator_name'] == db_entry['indicator_name'], "Indicator name harus sama"
            assert abs(row['value'] - db_entry['value']) < 0.001, "Value harus sama"

    def test_export_response_headers(self, populated_db):
        """Test response headers untuk export"""
        # Test CSV headers
        response = populated_db.get('/export?format=csv')
        assert 'Content-Disposition' in response.headers, "Harus ada Content-Disposition header"
        assert 'raw-data.csv' in response.headers['Content-Disposition'], "Filename harus raw-data.csv"
        assert 'text/csv' in response.content_type, "Content-Type harus text/csv"

        # Test Excel headers
        response = populated_db.get('/export?format=excel')
        assert 'Content-Disposition' in response.headers, "Harus ada Content-Disposition header"
        assert 'raw-data.xlsx' in response.headers['Content-Disposition'], "Filename harus raw-data.xlsx"
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.content_type, \
            "Content-Type harus Excel MIME type"


if __name__ == "__main__":
    # Jalankan test secara standalone
    pytest.main([__file__, "-v"])