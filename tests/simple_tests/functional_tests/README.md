# Functional Tests - BPS Data Management System

Testing fungsional sederhana untuk memverifikasi user flows utama sistem BPS Data Management.

## 📋 Test Coverage

### 1. **Landing Page Test** (`test_landing_page.py`)
- ✅ Verifikasi halaman utama dapat dimuat
- ✅ Menampilkan summary dan metadata dengan benar
- ✅ Handle kasus kosong (belum ada data)
- ✅ Response time dan content validation

### 2. **Upload Excel Test** (`test_upload_excel.py`)
- ✅ Upload file Excel valid
- ✅ Validasi format file (hanya .xls/.xlsx)
- ✅ Validasi metadata (uploader, version, data_type, time_period)
- ✅ Handle file kosong atau invalid
- ✅ Error handling untuk duplicate data
- ✅ Feedback sukses/gagal

### 3. **Manual Entry Test** (`test_manual_entry.py`)
- ✅ Form input manual data
- ✅ Validasi semua field wajib
- ✅ Support berbagai format periode (monthly: YYYY-MM, quarterly: YYYY-Q1, yearly: YYYY)
- ✅ Validasi format nilai (harus angka)
- ✅ Error handling dan feedback

### 4. **Dashboard Test** (`test_dashboard.py`)
- ✅ Tampilan data di dashboard (/preview-data)
- ✅ Filter berdasarkan uploader, data_type, time_period, indicator
- ✅ Pagination dengan berbagai limit
- ✅ Filter options tersedia
- ✅ Handle filter yang tidak menghasilkan data

### 5. **Export Test** (`test_export.py`)
- ✅ Export ke format CSV
- ✅ Export ke format Excel
- ✅ Filter data selama export
- ✅ Validasi headers dan content-type
- ✅ Data integrity validation
- ✅ Handle export kosong

## 🚀 Cara Menjalankan Tests

### Persiapan Environment

1. **Install dependencies:**
```bash
cd simple_tests/functional_tests/
pip install -r requirements.txt
```

2. **Pastikan aplikasi Flask berjalan:**
```bash
# Di terminal terpisah, jalankan aplikasi
cd /path/to/project
python app.py
# Aplikasi harus running di http://localhost:5000
```

### Menjalankan Tests

**Jalankan semua functional tests:**
```bash
# Dari root project directory
pytest simple_tests/functional_tests/ -v

# Atau dari folder functional_tests
cd simple_tests/functional_tests/
pytest -v
```

**Jalankan test spesifik:**
```bash
# Test tertentu
pytest test_landing_page.py -v
pytest test_upload_excel.py::TestUploadExcel::test_upload_valid_excel_file -v

# Dengan coverage report
pytest --cov=../.. --cov-report=html

# Dengan parallel execution (butuh pytest-xdist)
pytest -n 4
```

**Jalankan dengan benchmark (performance testing):**
```bash
pytest --benchmark-only --benchmark-columns='min,max,mean,stddev'
```

## 📊 Test Results dan Reporting

### HTML Report
```bash
pytest --html=report.html --self-contained-html
```

### Coverage Report
```bash
pytest --cov=. --cov-report=html
# Buka htmlcov/index.html di browser
```

### JSON Output (untuk CI/CD)
```bash
pytest --json=results.json
```

## 🛠️ Test Configuration

### `pytest.ini` (folder ini)

Gunakan section **`[pytest]`** (bukan `[tool:pytest]`) agar pytest memuat opsi lokal. Verifikasi cepat dari repo root: `python -m pytest tests/test_simple_tests_pytest_ini.py -q`, atau `cd tests/simple_tests/functional_tests` lalu `python -m pytest --collect-only -q`.

### Environment Variables
```bash
# Base URL aplikasi (default: http://localhost:5000)
export APP_BASE_URL=http://localhost:5000

# Timeout untuk requests (detik)
export REQUEST_TIMEOUT=10

# Enable verbose output
export TEST_VERBOSE=1
```

### Custom Test Data
Edit `conftest.py` untuk mengubah sample data atau test fixtures.

## 🧪 Test Utilities

### Helper Functions (`test_utils.py`)

```python
from test_utils import (
    create_sample_excel_file,      # Membuat file Excel test
    assert_response_success,       # Assert response status
    assert_page_contains_error,    # Assert error message
    assert_csv_content_valid,      # Validasi CSV content
    measure_response_time          # Performance measurement
)

# Contoh penggunaan
excel_file = create_sample_excel_file(get_sample_upload_data())
response, time_taken = measure_response_time(client.get, '/')
assert time_taken < 2.0  # Response harus < 2 detik
```

## 🎯 Best Practices

### ✅ Do's
- Jalankan tests secara teratur (setiap deployment)
- Monitor test execution time
- Review failed tests segera
- Update tests ketika ada perubahan UI/functionality
- Gunakan descriptive test names

### ❌ Don'ts
- Jangan skip tests tanpa alasan jelas
- Jangan hardcode values yang sering berubah
- Jangan membuat tests yang terlalu kompleks
- Jangan ignore test failures

## 📈 Performance Benchmarks

| Test | Expected Time | Status |
|------|---------------|---------|
| Landing Page | < 1s | ✅ |
| Dashboard Load | < 2s | ✅ |
| Export CSV (100 rows) | < 3s | ✅ |
| Upload Excel | < 5s | ✅ |

## 🐛 Debugging Failed Tests

### Common Issues

1. **Flask app tidak running:**
   ```bash
   # Start app dulu
   python app.py
   ```

2. **Database tidak terinisialisasi:**
   ```bash
   # Hapus data.db dan restart app
   rm data.db
   python app.py
   ```

3. **Port konflik:**
   ```bash
   # Change port di app.py atau kill process
   lsof -i :5000
   kill -9 <PID>
   ```

### Debug Mode
```bash
# Jalankan dengan debug output
pytest -v -s --tb=long

# Atau dengan PDB
pytest --pdb
```

## 🔧 Maintenance

### Menambah Test Baru
1. Ikuti struktur file yang ada
2. Gunakan fixtures dari `conftest.py`
3. Tambahkan helper functions di `test_utils.py` jika diperlukan
4. Update README.md

### Cleanup
```bash
# Hapus test artifacts
rm -rf *.xlsx *.csv __pycache__/
```

## 📞 Support

Untuk pertanyaan atau issues:
1. Check existing tests untuk examples
2. Review error messages dengan teliti
3. Pastikan environment setup benar
4. Update dependencies jika perlu

---

**Tim QA Internal** - BPS Data Management System