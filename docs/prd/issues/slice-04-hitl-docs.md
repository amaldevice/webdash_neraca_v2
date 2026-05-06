## Parent

#53 — PRD: Template Excel universal & penyederhanaan unggah data

## What to build

**HITL / kebijakan produk + dokumentasi:** keputusan apakah periode transisi membutuhkan **flag lingkungan** (atau cabang) agar unggah template lama (per `dataset_slug`) masih didukung; memperbarui **docs/CONTEXT** atau catatan domain/changelog internal bahwa pola pemilih **sheet sumber BI** bukan UX utama. Peringatan pemisah indikator (`|`) jika relevan, dirujuk di README template (bukan UI mapping delimiter).

## Acceptance criteria

- [ ] Keputusan tertulis: dukungan template lama ya/tidak dan mekanismenya
- [ ] Dokumentasi domain/konfigurasi memuat implikasi `dataset_slug` / `dataset_code` untuk unggah baru
- [ ] Jika flag transisi: dokumentasi operator untuk mengaktifkan/menonaktifkan

## Blocked by

- #55 — perilaku parse/intake harus jelas dulu
