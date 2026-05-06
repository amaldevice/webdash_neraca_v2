---
title: "PRD — Keandalan tes, semantik periode, dan pengerasan arsitektur"
status: draft
created: 2026-05-06
tracker: github
github_issue: https://github.com/amaldevice/webdash_neraca_v2/issues/47
child_issues:
  - https://github.com/amaldevice/webdash_neraca_v2/issues/48
  - https://github.com/amaldevice/webdash_neraca_v2/issues/49
  - https://github.com/amaldevice/webdash_neraca_v2/issues/50
  - https://github.com/amaldevice/webdash_neraca_v2/issues/51
labels: [needs-triage]
---

# PRD — Keandalan tes, semantik periode, dan pengerasan arsitektur

Dokumen ini memadukan temuan audit arsitektur, dead-code surface, dan hasil menjalankan ulang `pytest` pada lingkungan pengembangan. Kosakata domain mengikuti **docs/CONTEXT.md** (`dataset_code`, `period marker`, `upload_runs`, `data_type`, `time_period`, `data_entries`).

---

## Problem Statement

Dari sudut pandang **pengembang dan operator** internal:

1. **Suite tes tidak hijau penuh** pada konfigurasi umum: ada ketidaksesuaian antara ekspektasi tes dan perilaku parser untuk kombinasi **nilai periode polos + `time_period` triwulanan**, serta tes fungsional dashboard yang mengasumsikan urutan kolom HTML tetap sehingga gagal ketika tabel menampilkan label seperti teks indikator di posisi yang sama dengan asumsi lama.
2. **Menjalankan `pytest` tanpa mengatur DSN secara eksplisit** sering memakai `DATABASE_URL` dari berkas lingkungan (mis. server SQL jarak jauh), sehingga koleksi tes atau inisialisasi mesin DB gagal atau tidak deterministik — bukan perilaku yang diinginkan untuk loop umpan balik cepat.
3. **Dokumentasi dan rencana tertulis** masih menyebut modul atau alur yang sudah tidak ada, sehingga onboarding dan prioritas refactor salah arah.
4. **Arsitektur** menumpuk tanggung jawab di beberapa titik (kebijakan HTTP unggah, semantik `period marker` vs pembentukan filter query, penanganan error integritas lintas dialek SQL, permukaan publik paket parser) sehingga perubahan kecil menyebar luas dan sulit diuji secara terisolasi.

---

## Solution

Program kerja bertahap yang:

- Menetapkan **kontrak semantik** yang jelas untuk parsing periode (khususnya ambiguitas tahun saja di bawah mode `quarterly` / `yearly` / `monthly`) dan menyelaraskan **implementasi** dengan **tes** serta perilaku yang terdokumentasi untuk pengguna unggah dan input manual.
- Mengganti atau memperketat **tes yang rapuh** agar menguji perilaku yang terlihat pengguna (mis. memastikan kolom nilai numerik lewat header atau peran semantik), bukan indeks sel statis.
- Menstandarkan **bootstrap tes**: DSN SQLite terkendali untuk pytest tanpa bergantung pada urutan impor modul vs pemuatan `.env`.
- Merapikan **permukaan modul** (API publik parser vs internal), **mengurangi duplikasi normalisasi numerik**, dan **mengekstrak seam** untuk kebijakan unggah serta error persistensi agar regresi dapat dicegah dengan tes berfokus perilaku.
- **Menyinkronkan dokumentasi operasional** (panduan tes, plan Cursor, indeks docs) dengan pohon kode aktual.

---

## User Stories

1. Sebagai **pengembang backend**, saya ingin **`pytest` lokal selalu memakai basis data tes yang terkendali**, agar saya tidak perlu mengingat urutan impor atau interaksi `.env` dengan `DATABASE_URL` produksi.
2. Sebagai **pengembang backend**, saya ingin **satu perintah dokumentasi** yang menjamin DSN tes, agar onboarding rekan baru tidak tersandung error koneksi saat koleksi tes.
3. Sebagai **QA / pengembang**, saya ingin **semua tes hijau pada CI dan mesin dev** setelah checkout bersih, agar regresi terdeteksi segera.
4. Sebagai **steward data**, saya ingin **nilai `time_period` triwulanan untuk tahun saja** diinterpretasi konsisten di parser, pratinjau unggah, dan penyimpanan `data_entries`, agar laporan tidak bergeser diam-diam antar rilis.
5. Sebagai **pengguna input manual**, saya ingin **format periode yang saya masukkan** dipetakan ke tahun/bulan/kuartal dengan aturan yang sama seperti unggah Excel, agar tidak ada kejutan antara saluran input.
6. Sebagai **pengembang**, saya ingin **spesifikasi perilaku parser periode** tertulis dalam satu tempat (bukan tersebar di komentar tes saja), agar perubahan disengaja vs bug jelas.
7. Sebagai **pengembang frontend / integrasi**, saya ingin **tes HTML dashboard** mencari kolom berdasarkan makna (mis. nilai / indikator), agar perubahan urutan kolom UI yang sah tidak merusak suite.
8. Sebagai **pengguna halaman pratinjau**, saya ingin **tabel pratinjau** tetap dapat dibaca dan diuji tanpa asumsi indeks kolom kaku di tes.
9. Sebagai **operator server kantor**, saya ingin **dokumentasi tes** menjelaskan variabel lingkungan yang mempengaruhi pytest, agar skenario MySQL uji integrasi tidak tertukar dengan smoke lokal.
10. Sebagai **pengembang**, saya ingin **tes integrasi dialek** (MySQL/PostgreSQL) tetap opsional dan terpisah dari smoke SQLite cepat, agar pipeline default tetap ringan.
11. Sebagai **maintainer**, saya ingin **menghapus placeholder `assert True`** di jalur tes UI, agar tidak ada false sense of security.
12. Sebagai **maintainer**, saya ingin **placeholder print** di tes diganti asersi perilaku atau skip terdokumentasi, agar noise log CI berkurang.
13. Sebagai **pengembang**, saya ingin **API publik paket parser** kecil dan stabil, agar IDE autocomplete dan kontrak impor tidak mengekspos simbol internal.
14. Sebagai **pengembang**, saya ingin **satu implementasi konversi float** untuk jalur normalisasi dan mutasi yang konsisten, agar tidak ada drift angka antara unggah dan pembaruan DB.
15. Sebagai **pengembang**, saya ingin **seam tunggal** untuk error unique/integritas dari lapisan persistensi, agar penanganan unggah tidak mencampur dialek SQLite dan server SQL di banyak cabang.
16. Sebagai **pengembang keamanan internal**, saya ingin **kebijakan CSRF, rate limit, dan identitas klien unggah** dapat diuji tanpa meniru seluruh stack Flask di setiap tes rute, agar regresi kebijakan terisolasi.
17. Sebagai **pengembang**, saya ingin **parameter filter `period marker`** dibangun melalui modul yang sama untuk pratinjau, manajemen data, dan ekspor, agar konsistensi antarhalaman terjaga.
18. Sebagai **pengguna filter rentang periode**, saya ingin **start/end period** diterapkan sama di semua tampilan data, sesuai prinsip di CONTEXT.
19. Sebagai **reviewer PR**, saya ingin **dokumentasi plan Cursor** tidak menyebut modul yang sudah dihapus, agar review tidak membuang waktu mengejar hantu.
20. Sebagai **pengembang baru**, saya ingin **panduan TESTING** mencerminkan struktur tes dan perintah aktual, agar langkah pertama saya berhasil.
21. Sebagai **pengembang**, saya ingin **lapisan repositori daftar entri** memiliki alasan jelas (kedalaman) atau digabung, agar tidak ada hop sia-sia antara kueri dan pemanggil.
22. Sebagai **pengembang**, saya ingin **pemisahan** antara “arti periode untuk filter” dan “fragment SQL untuk filter”, agar perubahan aturan bisnis tidak merusak query builder sekaligus.
23. Sebagai **pengelola rilis**, saya ingin **changelog docs** mencatat penyelesaian PRD ini, agar operator tahu perilaku tes dan parser yang diperbarui.
24. Sebagai **pengembang**, saya ingin **optional static analysis** (unused import / dead export) di pipeline atau dokumentasi, agar dead code surface tidak menumpuk lagi.
25. Sebagai **pengguna alur unggah**, saya ingin **`upload_runs`** dan status unggah tetap akurat setelah refactor seam error, agar audit trail tidak rusak.
26. Sebagai **pengembang**, saya ingin **regresi untuk kasus edge periode** terkunci dalam tes parametrik yang mencerminkan kontrak bisnis, bukan implementasi tanggal internal library.
27. Sebagai **DevOps internal**, saya ingin **versi Python** untuk pengembangan lokal selaras dengan pin dependensi numerik, agar `pip install -r requirements.txt` tidak gagal diam-diam pada interpreter lama.
28. Sebagai **pemilik produk internal**, saya ingin **ruang lingkup PRD** jelas memisahkan perbaikan tes/dok dari fitur pengguna akhir, agar prioritas sprint tidak kabur.
29. Sebagai **pengembang**, saya ingin **issue tracker** memiliki label triage agar pekerjaan ini masuk alur prioritisasi normal.
30. Sebagai **auditor**, saya ingin **bukti tes hijau** dilampirkan pada PR penutup epic ini, agar klaim selesai terverifikasi.

---

## Implementation Decisions

- **Kontrak periode:** Menetapkan perilaku resmi untuk string tahun saja di bawah `time_period` `quarterly` (apakah `month` disetel atau `None`, dan bagaimana kuartal diturunkan) lalu menyelaraskan parser, mutasi, dan dokumentasi unggah/manual — tanpa mengubah data historis kecuali ada kebijakan migrasi eksplisit (di luar cakupan default PRD ini kecuali ditambahkan sebagai fase terpisah).
- **Bootstrap pytest:** Memastikan inisialisasi DSN untuk tes terjadi sebelum konfigurasi aplikasi membaca `.env` yang mengarah ke server jarak jauh, atau mendokumentasikan dan mengotomatiskan override eksplisit SQLite untuk pytest (satu keputusan teknis dipilih tim; keduanya memenuhi tujuan determinisme).
- **Tes dashboard / pratinjau:** Mengganti asersi berbasis indeks kolom dengan strategi berbasis struktur tabel yang stabil (header, `data-*`, atau urutan semantik yang dijamin template).
- **Seam persistensi:** Memusatkan interpretasi error integritas dari SQLAlchemy dan dialek asli ke adapter atau helper tunggal yang dipanggil lapisan layanan unggah.
- **Seam kebijakan HTTP unggah:** Mengekstrak validasi sesi, rate limit, dan parameter template dataset dari handler rute mentah ke modul atau callable yang dapat diuji dengan dependensi injeksi/monkeypatch terbatas.
- **Permukaan parser:** Mempersempit simbol diekspor publik; menyisakan impor internal untuk modul dalam paket yang sama.
- **Normalisasi numerik:** Menyatukan logika konversi float untuk jalur yang setara domain (mis. nilai sel numerik) agar satu sumber kebenaran.
- **Filter `period marker`:** Mempertimbangkan ekstraksi fungsi murni untuk membentuk rentang periode dari request, dipakai bersama oleh tampilan pratinjau, manajemen, dan ekspor.
- **Dokumentasi:** Memperbarui indeks docs dan rencana Cursor agar tidak mereferensikan fitur yang sudah dihapus; memisahkan arsip dari dokumen “sumber kebenaran” aktif.
- **Tidak ada perubahan skema wajib** dalam cakupan inti kecuali tim memutuskan migrasi data terpisah untuk memperbaiki baris historis yang salah interpretasi — jika demikian, itu menjadi sub-epik dengan rencana backfill sendiri.

---

## Testing Decisions

- **Prinsip:** Tes mengunci **perilaku luar** (output parser untuk pasangan input/`time_period`, isi respons HTML yang relevan bagi pengguna, kode status dan pesan error unggah), bukan struktur internal private kecuali melalui seam publik yang disengaja.
- **Modul yang ditargetkan tes:** Lapisan normalisasi periode dan nilai; pembentuk filter rentang periode; orkestrasi unggah (termasuk cabang error integritas); halaman pratinjau/manajemen yang memuat tabel data; helper bootstrap DB untuk pytest.
- **Prior art:** Tes parametrik periode yang sudah ada; pola `db_path` / `app_module` di konfigurasi pytest; smoke integrasi dialek jarak jauh sebagai lapisan terpisah dari tes cepat SQLite.

---

## Out of Scope

- Fitur produk baru untuk pengguna akhir (grafik baru, API publik eksternal, dll.).
- Migrasi data produksi massal kecuali diputus sebagai sub-proyek dengan PRD sendiri.
- Penggantian framework web atau migrasi dari Flask.
- Audit dead code otomatis penuh dengan skor formal (mis. worker audit eksternal) — hanya rekomendasi tooling opsional.

---

## Further Notes

- PRD ini berasal dari gabungan audit statis, eksplorasi arsitektur, dan eksekusi `pytest` dengan DSN SQLite eksplisit pada Python 3.11; dua kegagalan tes teridentifikasi sebelum pekerjaan perbaikan.
- **Triage GitHub:** https://github.com/amaldevice/webdash_neraca_v2/issues/47 (label `needs-triage`).
