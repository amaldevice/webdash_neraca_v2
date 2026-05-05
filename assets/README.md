# assets/

Folder ini berisi source style untuk build Tailwind yang dipakai aplikasi.

## Berkas

- `tailwind.css`
  - Source utama untuk pipeline Tailwind/DaisyUI.
  - Berisi `@tailwind base; @tailwind components; @tailwind utilities;` dan utility/komponen khusus proyek.
  - Hasil kompilasi disimpan ke `static/css/tailwind.css`.

## Catatan untuk agent

- Jika ingin ubah style global/utility, mulai dari file ini.
- Setelah edit, rebuild stylesheet (lihat perintah project build yang dipakai di README).
