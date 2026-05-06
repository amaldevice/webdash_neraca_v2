## Parent

#53 — PRD: Template Excel universal & penyederhanaan unggah data

## What to build

**Smoke / E2E ringan:** skenario minimal — gunakan fixture template universal → unggah → **pratinjau** muncul tanpa error (atau assert teks/elemen kunci). Mengikuti pola tes UI yang ada di repo. Memverifikasi form masih memakai token/CSRF seperti saat ini.

## Acceptance criteria

- [ ] Satu tes otomatis menutupi jalur unggah ke pratinjau untuk file universal
- [ ] Tes berjalan di CI atau diinstruksikan jalan lokal
- [ ] Melengkapi (tidak menggantikan) uji unit parser

## Blocked by

- #55 — parse harus siap
- #56 — UI unggah diselaraskan
