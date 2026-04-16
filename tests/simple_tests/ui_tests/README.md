# UI Tests - Browser Automation

Testing antarmuka pengguna menggunakan Chrome DevTools MCP untuk automasi browser.

## 📋 **Tujuan Testing**

- **Visual Testing**: Verifikasi tampilan UI dan layout
- **Navigation Testing**: Test navigasi antar halaman
- **Responsive Testing**: Test tampilan di berbagai ukuran layar
- **Screenshot Capture**: Capture visual state untuk verifikasi manual

## 🏗️ **Struktur Testing**

```
ui_tests/
├── test_browser_navigation.py    # Test navigasi halaman
├── test_form_interactions.py     # Test interaksi form & responsive
├── test_data_visualization.py    # Test visualisasi data
├── conftest.py                   # Konfigurasi pytest & fixtures
└── README.md                     # Dokumentasi ini
```

## 🚀 **Cara Menjalankan**

### **Prasyarat**
1. Chrome browser terinstall
2. Chrome DevTools MCP server aktif
3. Aplikasi Flask berjalan di `http://localhost:5000`

### **Menjalankan UI Tests**
```bash
cd simple_tests/ui_tests
pytest -v

# Dengan screenshot capture
pytest -v --capture-screenshots

# Jalankan test spesifik
pytest test_browser_navigation.py -v
pytest test_form_interactions.py -v
```

## 🧪 **Kategori Test**

### **1. Browser Navigation**
- ✅ Load halaman utama
- ✅ Navigasi ke dashboard
- ✅ Navigasi ke halaman manual entry
- ✅ Navigasi ke halaman upload
- ✅ Test fungsi refresh halaman

### **2. Form Interactions**
- ✅ Display form manual entry
- ✅ Display form upload
- ✅ Display filter dashboard
- ✅ Responsive design (mobile/tablet)
- ✅ Page zoom functionality

### **3. Data Visualization**
- ✅ Summary display di landing page
- ✅ Data table di dashboard
- ✅ Visualization widget di dashboard (summary cards + analisis rentang)
- ✅ Export buttons visibility
- ✅ Empty state display
- ✅ Filter UI interaction
- ✅ Loading states

## 🛠️ **Tools Yang Digunakan**

- **Chrome DevTools MCP**: Browser automation & screenshot capture
- **pytest**: Test framework dengan fixtures
- **Screenshot Capture**: Automatic capture untuk verifikasi visual

## 📊 **Screenshot Output**

Screenshot disimpan di folder `screenshots/` dengan format:
```
test_name_YYYYMMDD_HHMMSS.png
```

Contoh:
- `landing_page_load_20260227_143052.png`
- `dashboard_table_20260227_143105.png`
- `mobile_responsive_20260227_143112.png`

## ⚙️ **Konfigurasi**

Edit `test_config.py` untuk mengubah:
- **Base URL**: URL aplikasi Flask
- **Window sizes**: Ukuran viewport untuk responsive testing
- **Screenshot settings**: Enable/disable capture screenshot
- **Timeout settings**: Waktu tunggu untuk page load

## 🎯 **Markers pytest**

```bash
# Jalankan hanya UI tests
pytest -m ui

# Jalankan hanya Chrome DevTools tests
pytest -m chrome

# Jalankan visual regression tests
pytest -m visual
```

## 📝 **Menambah Test Baru**

1. Buat file test baru dengan prefix `test_`
2. Gunakan fixtures dari `conftest.py`
3. Import `CallMcpTool` untuk Chrome DevTools API
4. Gunakan `get_screenshot_path()` untuk capture screenshot
5. Add markers yang sesuai (`@pytest.mark.ui`, `@pytest.mark.chrome`)

## 🔧 **Troubleshooting**

### **Chrome DevTools Tidak Connect**
```
❌ Chrome DevTools MCP server tidak aktif
✅ Pastikan Chrome DevTools MCP server berjalan
✅ Cek konfigurasi server di Cursor settings
```

### **Screenshot Gagal**
```
❌ Screenshot capture failed
✅ Cek permission write di folder screenshots/
✅ Pastikan Chrome DevTools dapat mengakses filesystem
```

### **Page Load Timeout**
```
❌ Page load timeout
✅ Periksa aplikasi Flask berjalan di port 5000
✅ Cek koneksi network ke localhost
✅ Increase timeout di test_config.py
```

## 📊 **Test Results**

Setiap test akan menghasilkan:
- ✅ **PASS**: Test berhasil
- ❌ **FAIL**: Test gagal dengan detail error
- 📸 **Screenshot**: Visual capture untuk verifikasi

## 🎯 **Best Practices**

1. **Screenshot Naming**: Gunakan nama deskriptif untuk screenshot
2. **Wait Times**: Berikan waktu yang cukup untuk page/content load
3. **Error Handling**: Tangkap exception dengan pesan yang jelas
4. **Cleanup**: Pastikan browser state clean antara tests
5. **Responsive Testing**: Test multiple viewport sizes

## 📞 **Support**

Untuk troubleshooting:
1. Cek log pytest untuk error details
2. Review screenshot di folder `screenshots/`
3. Verifikasi Chrome DevTools MCP server status
4. Pastikan aplikasi target dapat diakses