## Parent

#53 — PRD: Template Excel universal & penyederhanaan unggah data

## What to build

Penyederhanaan **UI halaman Unggah**: hilangkan pemilih **dataset / sheet sumber BI** dan daftar unduh per-dataset; tampilkan **satu** CTA **Unduh template universal** (mengarah ke hasil slice template) + teks bantuan singkat. **Tidak ada** input One Way / Two Way / Three Way. **Flow / Stock** (`data_type`) dan **Pengunggah** (serta field waktu periode form yang relevan) tetap. Form POST bekerja dengan slice parse universal (tanpa memaksa `dataset_slug` lama, kecuali kebijakan transisi di issue HITL terpisah).

## Acceptance criteria

- [ ] Satu area unduh template universal terlihat jelas (bukan tersebar di banyak link per label dataset)
- [ ] Kontrol One/Two/Three Way tidak ditampilkan
- [ ] Pilihan Flow/Stock dan pengunggah tetap ada
- [ ] Pengguna dapat menyelesaikan unggah + pratinjau memakai file universal tanpa memilih lembar BI

## Blocked by

- #54 — file & endpoint unduh
- #55 — parse/pratinjau universal
