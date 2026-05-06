# PRD: Template Excel universal & penyederhanaan unggah data

**Status draf** · Dibuat dari kebutuhan produk: satu template, instruksi di berkas, UI tanpa klasifikasi One/Two/Three Way; `data_type` Flow/Stock tetap.  
**Triage label usulan (issue tracker):** `needs-triage`  
**Kosakata domain:** lihat [docs/CONTEXT.md](../CONTEXT.md) (`dataset_code`, `dataset_slug`, `data_type`, `time_period`, `uploader_name`).

---

## Problem Statement

Pengguna unggah saat ini dihadapkan pada banyak pilihan dataset/sheet sumber BI dan banyak unduhan template per `dataset_slug`, sehingga membingungkan bila sumber data sebenarnya beragam (BPJS, PLN, BI, real estate, dll.) tetapi ingin disatukan ke dalam satu pola entri. Selain itu, meminta pengguna memahami perbedaan tabel *one way* / *two way* / *three way* di UI menambah beban kognitif, padahal dimensi ganda sudah dapat diwakili di satu kolom indikator bertingkat. Dibutuhkan **satu template Excel yang ringkas** berisi **panduan pengisian**, serta **satu alur unggah** yang jelas: nama dataset, indikator, periode, nilai, dan pilihan jenis data Flow/Stock—tanpa memilih lembar sumber BI per katalog lama.

---

## Solution

1. **Satu template universal** (satu lembar data + lembar/dokumentasi penjelasan cara isi) yang kolom utamanya: **Nama Dataset** (kolom pertama), **Indikator** (teks; bagian multi-dimensi dipisah pemisah yang didokumentasikan, mis. `|`), **Periode** (mendukung `YYYY`, `YYYY-MM`, `YYYY-Q1`, `YYYY-MM-DD` sesuai kebijakan periode), **Nilai** (numerik).  
2. **Form unggah web** disederhanakan: tidak ada input One/Two/Three Way; **Jenis data Flow / Stock** (`data_type`) tetap dipilih di form; **pilihan dataset per `source_sheet` BI** dan teks bantuan “sheet sumber” dihilangkan diganti **satu tautan/aksi “Unduh template universal”** dengan penjelasan singkat.  
3. **Backend** mengenali skema long universal ini (satu “keluarga” definisi data / normalisasi ke `data_entries`) sehingga parser dan validasi mengikuti kolom template baru, bukan header per-dataset REKAP BI.  
4. **Instruksi** wajib tersedia **di dalam berkas template** (mis. lembar README di workbook) agar pengguna offline tetap punya panduan.

---

## User Stories

1. Sebagai **operator data**, saya ingin **mengunduh satu template Excel** untuk semua jenis laporan, agar tidak harus memilih banyak template berbeda.  
2. Sebagai **operator data**, saya ingin **membaca panduan pengisian di dalam file template**, agar saya bisa mengisi tanpa membuka dokumentasi web.  
3. Sebagai **operator data**, saya ingin **kolom pertama berisi nama dataset** yang saya tentukan (mis. PLN, BI), agar baris mudah dikelompokkan dan dikenali.  
4. Sebagai **operator data**, saya ingin **satu kolom Indikator** untuk gabungan dimensi dengan pemisah yang jelas, agar tidak harus mengisi banyak kolom seperti template REKAP lamanya.  
5. Sebagai **operator data**, saya ingin **memasukkan periode dalam beberapa format umum** (tahun, bulan, triwulan, tanggal), agar konsisten dengan cara kerja laporan saya.  
6. Sebagai **operator data**, saya ingin **memilih Flow atau Stock** saat unggah, agar metadata akuntansi tetap benar.  
7. Sebagai **operator data**, saya **tidak ingin** diminta memilih **One Way / Two Way / Three Way** di layar, agar formulir lebih ringkas.  
8. Sebagai **operator data**, saya ingin **menghapus langkah memilih dataset yang mengikat nama sheet BI**, agar tidak salah sheet ketika sumber saya bukan format BI.  
9. Sebagai **operator data**, saya ingin **tautan unduh template universal** terlihat jelas di halaman unggah, agar saya tidak mencari di footer atau dokumen terpisah.  
10. Sebagai **administrator sistem**, saya ingin **template pendek dan konsisten**, agar pelatihan pengguna baru lebih cepat.  
11. Sebagai **pengembang**, saya ingin **satu jalur parse long** dengan header tetap, agar pengujian dan pemeliharaan lebih mudah.  
12. Sebagai **pengembang**, saya ingin **validasi baris** yang jelas (nama dataset tidak kosong, indikator tidak kosong, periode dapat dinormalisasi, nilai numerik), agar kesalahan input terdeteksi di pratinjau.  
13. Sebagai **operator data**, saya ingin **pratinjau unggah** tetap menunjukkan ringkasan kesalahan baris, agar saya bisa memperbaiki Excel sebelum menyimpan.  
14. Sebagai **operator data**, saya ingin **nama pengunggah** tetap dicatat untuk audit, agar jejak tanggung jawab tidak hilang.  
15. Sebagai **administrator**, saya ingin opsi **environment** untuk masa transisi (mis. tetap mengizinkan unggah template lama) **dirancang**, agah migrasi bertahap dimungkinkan—jika tim memutuskan mendukung itu.  
16. Sebagai **pengguna**, saya ingin **pesan galat** dalam Bahasa Indonesia yang memuat nama kolom template universal, agar saya tahu apa yang diperbaiki.  
17. Sebagai **operator data**, saya ingin **memahami bahwa pemisah indikator** (mis. `|`) tidak boleh bentrok dengan teks indikator saya, atau mendapat peringatan jika bentrok.  
18. Sebagai **produser laporan**, saya ingin **filter dan ekspor** downstream tetap bisa membedakan baris berdasarkan **nama dataset** yang tertulis di Excel, agar pivot tidak tercampur.  
19. Sebagai **pengembang**, saya ingin **uji unit** pada normalisasi periode dari string sel template, agar regresi format tanggal tidak mengembalikan data salah diam-diam.  
20. Sebagai **pengembang**, saya ingin **uji unit** pada pembentukan string metrik/indikator untuk penyimpanan konsisten dengan baris sumber.  
21. Sebagai **QA**, saya ingin **uji alur unggah end-to-end** (minimal pratinjau) untuk template universal, agah regresi UI terdeteksi.  
22. Sebagai **operator data**, saya ingin halaman unggah tetap **aman dari CSRF/token** seperti sekarang, agar tidak membuka celah keamanan saat form berubah.  
23. Sebagai **administrator**, saya ingin dokumentasi `CONTEXT`/changelog internal mencatat bahwa **`dataset_slug` sebagai pemilih sheet BI** tidak lagi menjadi pola utama di UX baru, agah konsistensi dokumen domain terjaga.  
24. Sebagai **pengguna**, saya ingin **ukuran file template kecil dan satu lembar data utama**, agar mudah diedit di laptop kantor.  
25. Sebagai **tim produk**, saya ingin **ruang lingkup luar** (parser workbook pemerintah dengan banyak header bertingkat) **tidak dicampur** dengan fitur ini, agah pengiriman fitur utama tidak tertunda.

*(Stories 15 dan 25 bersifat kebijakan—implementasi bisa menyesuaikan keputusan migrasi.)*

---

## Implementation Decisions

- **Model data unggah:** satu skema **long** dengan kolom konseptual `nama_dataset`, `indikator`, `periode`, `nilai`; penyimpanan internal tetap mengikuti kontrak `data_entries` (metrik/indikator sebagai string; periode dinormalisasi ke konvensi yang sudah dipakai aplikasi untuk filter dan ekspor).  
- **UI halaman Unggah:** hapus kontrol atau penyebutan **One Way / Two Way / Three Way**; pertahankan **`data_type`** **Flow / Stock**; ganti area pemilih dataset berbasis katalog sheet BI menjadi **satu entri unduhan template universal** + salinan instruksi singkat di halaman. Kolom pertama berkas = **Nama Dataset** sesuai permintaan produk.  
- **Generator template:** satu pembuat workbook dengan lembar panduan isian + satu lembar data dengan sedikit baris contoh opsional; tidak lagi mengharuskan pengguna mengunduh banyak varian per lembar BI.  
- **Parser unggah:** cabang parse utama untuk jalur baru membaca header universal (case-insensitive / alias dapat ditentukan); fallback ke perilaku lama hanya jika kebijakan migrasi mengharuskan dukungan ganda.  
- **Validasi:** input baris wajib untuk nama dataset, indikator, periode ter-parse, nilai numerik; integrasi dengan pratinjau unggah yang ada.  
- **Konfigurasi migrasi (opsional):** flag lingkungan atau keputusan produk untuk mengizinkan template dataset-lama dalam periode transisi—keputusan eksplisit, default mengarah **template universal saja** unless stated otherwise.  
- **Route/API:** endpoint pengunduhan template menjadi **satu endpoint universal** (nama dapat stabil seperti “template universal”); penghentian atau penyembunyian tautan per-dataset merupakan keputusan rilis—PRD meng asumsikan **UI utama** hanya menonjolkan universal.  
- **Layer parser:** modul normalisasi **periode fleksibel** dan **string indikator** dipisah sebagai perilaku yang dapat diuji tanpa Flask request context bila memungkinkan.

*Tidak menyertakan path file atau cuplikan kode di PRD ini.*

---

## Testing Decisions

- **Prinsip:** uji perilaku **luar** modul—keluaran parse, pesan validasi, dan byte workbook template—bukan struktur internal kelas.  
- **Modul yang diuji:** normalisasi periode dari string; validasi baris template universal; generator workbook (header dan kehadiran lembar panduan); integrasi ringan alur `parse → pratinjau` dengan fixture Excel minimal.  
- **Prior art:** pola pengujian yang ada untuk alur unggah/pratinjau dan tes Excel parser long-format di suite yang sudah ada—diperluas untuk skema kolom baru tanpa mengunci pada nama variabel internal.

---

## Out of Scope

- Konversi otomatis dari berkas pemerintah/publikasi dengan banyak header bertingkat atau blok lembar ke template universal (itu jalur transform terpisah atau pekerjaan manual).  
- UI pemetaan delimiter indikator per pengguna (kecuali ditambahkan iterasi berikutnya).  
- Perubahan skema basis data besar di luar apa yang sudah didukung penyimpanan entri numerik + metadata yang ada—kecuali direview secara eksplisit dalam tugas migrasi terpisah.

---

## Further Notes

- **Sinkron dokumentasi:** setelah implementasi disetujui, pembaruan ringkas changelog/README dokumen proyek mengikuti kebijakan repo (stub `planning`/README).  
- **Issue tracker:** pasangkan label **`needs-triage`** pada issue yang membawa PRD ini ke sistem backlog organisasi.  
- **Konfirmasi modul & tes:** tim engineering meninjau daftar modul di atas dan menandai mana yang **wajib** punya tes otomatis pertama (disarankan: normalisasi periode + validasi baris + satu tes generator template).

---

## Check-in produk (non-blocking)

Sesuaikan ekspektasi kamu dengan daftar modul di **Implementation Decisions**: tambah/kurangi scope migrasi template lama, dan tentukan apakah tes wajib pertama = normalisasi periode + generator template saja, atau termasuk satu E2E smoke unggah.
