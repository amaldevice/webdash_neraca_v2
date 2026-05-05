# Changelog

Semua perubahan ditulis ringkas untuk memudahkan pelacakan progres (internal).

## Unreleased (branch: `feature/ui-bootstrap-polish`)

### UI/UX (Bootstrap 5)
- Mengadopsi **Bootstrap 5 (via CDN)** untuk menstandarkan tampilan komponen (form, tombol, kartu, tabel) dan membuat layout lebih rapi & responsif.
- Merapikan halaman:
  - Landing
  - Unggah Excel
  - Input Manual
  - Pratinjau Data + Ekspor
  - Manajemen Data
  - Analisis/Agregasi

### Stabilitas UI
- Memperbaiki error JavaScript pada halaman **Unggah** (fungsi `updatePeriodFormat()`), sehingga tidak error ketika elemen tanggal periode tidak tersedia pada mode unggah.

### Bahasa UI
- Melokalkan seluruh teks UI menjadi **Bahasa Indonesia** dengan gaya **korporat & profesional**.
- Menyeragamkan istilah:
  - **Pengunggah**, **Versi**
  - Periode: **Bulanan / Triwulanan / Tahunan**
  - Tetap memakai **Flow/Stock** disertai keterangan ringkas: *Flow = arus, Stock = posisi*.

### Testing & QA
- Menambahkan/merapikan kerangka **testing & QA** (pytest core tests, dokumen QA checklist, dan artefak bug-hunting) pada commit sebelumnya.

## Riwayat commit kunci

- `de7f9d6` — Lokalisasi teks UI ke Bahasa Indonesia (templates + flash message)
- `c7cd6d9` — Refresh UI dengan Bootstrap 5 + hardening upload period format (fix JS error)
- `e1132ec` — Enhanced testing framework and bug fixes
- `fcaad59` — Complete testing framework and QA improvements
- `df79ecd` — Merge: feature/tests-qa
