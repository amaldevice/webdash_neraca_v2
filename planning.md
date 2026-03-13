
## Dokumentasi Ringkas Kode
- **Status**: selesai pada fase akhir.
- **Perubahan**: menambahkan OVERVIEW.md di root sebagai peta cepat folder (ssets, 	emplates, static) dan file Python inti (pp.py, ggregator.py, excel_parser.py, models.py).

- Fitur terbaru:
  - Parser Excel sudah di-advance ke alur preview: mendukung deteksi layout campuran/metadata, normalisasi angka lokal, dan `parse_excel_payload` dengan ringkasan diagnostics (`layout`, `header_row`, `warnings`, `invalid_rows`, `sample`).
  - Upload halaman `Upload` diubah jadi dua tahap: pratinjau terlebih dulu lalu konfirmasi sebelum insert.
  - Opsi override layout (`auto`/`vertical`/`horizontal`) ditambahkan pada form upload.
  - Validasi duplikasi dilakukan sebelum insert terhadap kombinasi `uploader + version + indicator + year + month + quarter`; duplikasi ditampilkan di pratinjau.
  - Pratinjau kini menyediakan opsi lewati data duplikasi secara granular per baris kandidat duplikasi (checkbox per row), termasuk kontrol cepat "Pilih Semua", "Batal Semua", dan "Balik Pilihan" + ringkasan jumlah pilihan agar user tahu kandidat yang dikecualikan.
  - Sistem notifikasi upload ditata ulang agar lebih stabil: posisi tetap di area atas halaman, lebar adaptif tidak mengganggu layout form, dan teks terbungkus rapi tanpa menimpa komponen lain.

- **Dokumentasi detail:** OVERVIEW.md kini memuat ringkasan per-folder (ssets, 	emplates, static) dan ringkasan operasional setiap file utama Python untuk keperluan onboarding/refactor cepat.
- [x] Buat dokumentasi detail per-folder: `assets/README.md`, `static/README.md`, `templates/README.md`, `templates/partials/README.md`.
- [x] Buat dokumentasi gabungan untuk semua berkas Python di `PY_FILES.md`.
- [x] Sinkronisasi pembaruan dokumentasi ini ke `planning.md` dan `C:/Users/PENGOLAHAN/.cursor/plans/bps_data_management_system_bd94389d.plan.md`.
