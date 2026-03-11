# static/

Folder aset yang di-serve langsung oleh Flask ke browser.

## Berkas

- `css/tailwind.css`
  - Hasil build dari `assets/tailwind.css`.
  - Dimuat langsung di `base_tailwind.html` bersama `css/style.css`.
- `css/style.css`
  - CSS kustom proyek (override dan komponen UI).
  - Menangani styling tabel, panel, topbar, badge status, fokus aksesibilitas, dan gaya interaksi.

## Kapan dipakai

- `tailwind.css`: baseline visual dan utility dari Tailwind + DaisyUI.
- `style.css`: lapisan style lanjutan agar UI lebih konsisten antar halaman.
