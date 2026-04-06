# Bug Tests - BPS Data Management System

Testing suite untuk edge cases, security vulnerabilities, dan potensi bugs pada sistem BPS Data Management.

## Struktur Test

```
simple_tests/bug_tests/
├── conftest.py              # Konfigurasi pytest dan fixtures
├── test_validation.py       # Input validation & boundary values
├── test_error_handling.py   # Error scenarios & exception handling
├── test_security.py         # Security vulnerabilities (XSS, SQL injection, etc.)
├── test_edge_cases.py       # Edge cases (empty data, large files, encoding)
├── test_concurrency.py      # Race conditions & concurrent access
└── README.md               # Dokumentasi ini
```

## Kategori Testing

### 1. Input Validation (`test_validation.py`)
- **Invalid file extensions**: Test upload dengan ekstensi file yang tidak valid
- **Empty required fields**: Test field wajib yang kosong
- **Invalid data types**: Test nilai data_type yang tidak valid
- **Boundary values**: Test batas maksimum file size dan nilai ekstrem
- **Malformed Excel files**: Test file Excel yang korup atau malformed
- **Special characters**: Test karakter spesial dalam input
- **SQL injection attempts**: Test percobaan SQL injection
- **XSS attempts**: Test percobaan XSS injection

### 2. Error Handling (`test_error_handling.py`)
- **Database connection failures**: Test kegagalan koneksi database
- **Integrity constraint violations**: Test pelanggaran constraint unik
- **File system permission denied**: Test masalah permission file system
- **Memory errors**: Test kesalahan memory (OutOfMemory)
- **Network timeouts**: Test timeout jaringan
- **Partial failures**: Test kegagalan sebagian dalam operasi bulk

### 3. Security Vulnerabilities (`test_security.py`)
- **SQL Injection**: Test injeksi SQL dalam semua input fields
- **XSS (Cross-Site Scripting)**: Test injeksi script dalam form fields
- **CSRF Protection**: Test validasi token CSRF (akan gagal - vulnerability)
- **File Upload Vulnerabilities**: Test path traversal, null byte injection
- **Information Disclosure**: Test kebocoran informasi dalam error messages
- **Rate Limiting**: Test perlindungan terhadap DoS attacks (akan gagal - vulnerability)
- **Session Security**: Test konfigurasi session cookies

### 4. Edge Cases (`test_edge_cases.py`)
- **Empty Excel files**: Test file Excel kosong
- **Files with only headers**: Test file hanya berisi header
- **Empty rows**: Test baris kosong dalam data
- **Large files**: Test file melebihi batas 16MB
- **Special characters**: Test Unicode dan emoji
- **Corrupted files**: Test file yang korup saat upload
- **Network timeouts**: Test simulasi timeout
- **Complex Excel structures**: Test file dengan multiple sheets, merged cells, formulas

### 5. Concurrency (`test_concurrency.py`)
- **Concurrent uploads**: Test upload bersamaan dengan data sama
- **Bulk operations**: Test operasi bulk bersamaan
- **Read-write conflicts**: Test konflik baca-tulis bersamaan
- **Database connection pooling**: Test pool koneksi database
- **File system concurrent writes**: Test penulisan file bersamaan
- **Session isolation**: Test isolasi session antar user
- **Memory usage**: Test penggunaan memory saat operasi bersamaan

## Cara Menjalankan Tests

### Jalankan Semua Bug Tests
```bash
# Dari root directory project
cd simple_tests/bug_tests
pytest

# Atau dari root directory
pytest simple_tests/bug_tests/
```

### Jalankan Kategori Test Tertentu
```bash
# Test validation saja
pytest simple_tests/bug_tests/test_validation.py

# Test security saja
pytest simple_tests/bug_tests/test_security.py

# Test concurrency saja
pytest simple_tests/bug_tests/test_concurrency.py -v
```

### Jalankan dengan Verbose Output
```bash
pytest simple_tests/bug_tests/ -v --tb=short
```

### Jalankan dengan Coverage
```bash
pytest simple_tests/bug_tests/ --cov=.. --cov-report=html
```

## Severity Levels

Setiap test yang mendeteksi vulnerability akan memberikan feedback dengan severity level:

- **CRITICAL**: Vulnerability yang dapat menyebabkan kerusakan serius (data loss, system compromise)
- **HIGH**: Vulnerability yang dapat dieksploitasi untuk mendapatkan akses tidak sah
- **MEDIUM**: Vulnerability yang dapat menyebabkan masalah operasional
- **LOW**: Vulnerability minor yang perlu diperbaiki

## Expected Failures

Beberapa test **diharapkan gagal** karena mendeteksi vulnerability yang ada:

### Security Vulnerabilities (akan gagal):
- `test_csrf_token_validation_missing`: Tidak ada CSRF protection
- `test_rate_limiting_bypass`: Tidak ada rate limiting
- `test_session_hijacking_simulation`: Session cookies tidak HttpOnly

### Error Handling (mungkin gagal):
- Tests yang mensimulasikan failure scenarios mungkin gagal jika error handling tidak robust

## Recommendations

Berdasarkan hasil testing, prioritaskan perbaikan berikut:

1. **Implement CSRF Protection**: Tambahkan CSRF tokens untuk semua form POST
2. **Add Rate Limiting**: Implementasi rate limiting untuk mencegah DoS attacks
3. **Secure Session Configuration**: Set session cookies sebagai HttpOnly dan Secure
4. **Input Sanitization**: Tambahkan sanitasi input untuk mencegah XSS
5. **SQL Parameterization**: Pastikan semua query menggunakan parameterized queries
6. **File Upload Security**: Validasi proper untuk file uploads
7. **Error Handling**: Improve error handling untuk graceful failures

## Test Fixtures

### Available Fixtures:
- `test_client`: Flask test client dengan database temporary
- `populated_db`: Database yang sudah terisi sample data
- `large_excel_file`: File Excel besar untuk testing size limits
- `malicious_file`: File dengan content malicious untuk security testing
- `invalid_file`: File dengan ekstensi tidak valid

## Dependencies

Pastikan dependencies berikut terinstall:
```bash
pip install pytest pytest-cov flask pandas openpyxl
```

## Integration dengan CI/CD

Untuk integrasi dengan pipeline CI/CD:

```yaml
# Contoh GitHub Actions
- name: Run Bug Tests
  run: |
    cd simple_tests/bug_tests
    pytest --tb=short --junitxml=bug_tests_results.xml

- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: bug-tests-results
    path: simple_tests/bug_tests/bug_tests_results.xml
```

## Contributing

Untuk menambah test baru:
1. Ikuti naming convention: `test_<kategori>_<deskripsi>`
2. Tambahkan docstring yang jelas
3. Sertakan severity level untuk security tests
4. Pastikan test dapat berjalan secara independent
5. Update dokumentasi ini jika menambah kategori baru