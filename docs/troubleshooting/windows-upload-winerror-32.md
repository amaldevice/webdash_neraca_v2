# Windows: `PermissionError` / WinError 32 saat unggah Excel

## Gejala

- Pesan seperti: `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: '…\\uploads\\<uuid>_template_….xlsx'`
- Muncul setelah **Unggah & Pratinjau** atau **Konfirmasi & Simpan**, sering saat aplikasi hendak **menghapus** file sementara di folder `uploads/`.

## Penyebab

Di Windows, file yang masih punya **handle terbuka** (misalnya workbook dibuka lewat `pandas` / `openpyxl`) tidak boleh dihapus atau diganti sampai handle ditutup. Parser memakai `pd.ExcelFile(path)`; bila objek itu tidak ditutup segera (misalnya tanpa `with`), handle bisa tetap hidup sampai garbage collection — sementara alur upload sudah memanggil `os.remove` pada path yang sama → WinError 32.

## Perbaikan di kode (repo)

`excel_parser/payload.py`: `_resolve_read_sheet` dan cabang error “lembar tidak ditemukan” memakai `with pd.ExcelFile(...) as xl:` agar file tertutup sebelum `pd.read_excel` berikutnya atau sebelum `os.remove`.

## Mitigasi operasional

1. **Jangan** buka file yang sama di Excel desktop sambil menguji unggah dari browser (dua proses = lock).
2. Pastikan antivirus / indexer tidak mem-lock file di `uploads/` saat deteksi real-time (jarang, tapi mungkin).
3. Setelah deploy perbaikan parser, restart worker Flask/Gunicorn sekali agar memuat modul baru.

## Verifikasi

Unggah file kecil → pratinjau → konfirmasi simpan; file di `uploads/` harus terhapus tanpa error. Ulangi 2–3 kali berturut-turut.

## Rujukan kode

- `excel_parser/payload.py` — `_resolve_read_sheet`, `parse_excel_payload`
- `services/upload_flow.py` — `os.remove` pada path unggah setelah sukses / error
- `services/upload_preview.py` — `_safe_remove_uploaded_file`
