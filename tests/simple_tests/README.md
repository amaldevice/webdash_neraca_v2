# Simple Testing Suite - BPS Data Management System

Testing sederhana untuk sistem manajemen data BPS yang digunakan oleh tim internal (<8 orang).

## 📋 **Tujuan Testing**

- **Functional Testing**: Menguji semua fitur utama aplikasi
- **UI Testing**: Menguji interaksi user melalui browser
- **Smoke Testing**: Verifikasi aplikasi berjalan normal
- **Edge Case Testing**: Menguji kondisi-kondisi khusus

## 🏗️ **Struktur Testing**

```
simple_tests/
├── README.md              # Dokumentasi ini
├── run_tests.py          # Script utama untuk menjalankan semua test
├── test_config.py        # Konfigurasi testing (URL, credentials, dll)
├── functional_tests/     # Test fungsional dengan qa-agent
│   ├── test_landing_page.py
│   ├── test_upload_excel.py
│   ├── test_manual_entry.py
│   ├── test_dashboard.py
│   └── test_export.py
├── ui_tests/            # Test UI dengan Chrome DevTools
│   ├── test_browser_navigation.py
│   ├── test_form_interactions.py
│   └── test_data_visualization.py
└── bug_tests/           # Test edge cases dengan bug-hunter
    ├── test_error_handling.py
    ├── test_validation.py
    └── test_edge_cases.py
```

## 🚀 **Cara Menjalankan**

### **Prasyarat**
1. Pastikan aplikasi Flask berjalan di `http://localhost:5000`
2. Install dependencies: `pip install -r requirements.txt`

### **Menjalankan Semua Test**
```bash
cd simple_tests
python run_tests.py
```

### **Menjalankan Test Spesifik**
```bash
# Test fungsional saja
python run_tests.py --test functional

# Test UI saja
python run_tests.py --test ui

# Test bug saja
python run_tests.py --test bug
```

### **Opsi Tambahan**
```bash
# Output verbose
python run_tests.py --verbose

# Generate HTML report (functional tests only)
python run_tests.py --html-report

# Combine options
python run_tests.py --test functional --verbose --html-report
```

## 🧪 **Jenis Test**

### **1. Functional Tests (qa-agent)**
- Test landing page dan summary
- Test upload file Excel
- Test input manual data
- Test dashboard filtering
- Test export CSV/Excel

### **2. UI Tests (Chrome DevTools MCP)**
- Test navigasi browser
- Test interaksi form
- Test visualisasi data
- Screenshot capture untuk verifikasi

### **3. Bug Tests (bug-hunter)**
- Test error handling
- Test validasi input
- Test edge cases
- Test security vulnerabilities

## 📊 **Test Results**

Setiap test akan menghasilkan:
- ✅ **PASS**: Test berhasil
- ❌ **FAIL**: Test gagal dengan detail error
- 📸 **Screenshot**: Capture layar untuk verifikasi manual

## 🛠️ **Tools Yang Digunakan**

- **qa-agent**: Testing fungsional otomatis
- **bug-hunter**: Testing keamanan dan edge cases
- **Chrome DevTools MCP**: Browser automation untuk UI testing
- **pytest**: Test framework
- **requests**: HTTP testing

## 🔧 **Konfigurasi**

Edit `test_config.py` untuk mengubah:
- Base URL aplikasi
- Test data
- Timeout settings
- Screenshot paths

## 📝 **Menambah Test Baru**

1. Buat file test baru di folder yang sesuai
2. Ikuti naming convention: `test_*.py`
3. Gunakan fixtures dari `test_config.py`
4. Tambahkan dokumentasi dan assertions yang jelas

## ⚠️ **Catatan Penting**

- Test ini untuk penggunaan internal tim saja
- Tidak untuk production deployment
- Jalankan test di environment development
- Backup database sebelum menjalankan test yang mengubah data

## 📞 **Support**

Untuk pertanyaan atau issues:
1. Cek log test di `test_results/`
2. Lihat screenshot di `screenshots/`
3. Periksa konfigurasi di `test_config.py`