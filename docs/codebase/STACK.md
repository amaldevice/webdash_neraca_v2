# Tech Stack Audit — BPS Data Management System

## Runtime Stack

- **Python**: 3.12+ (terdapat dukungan `alembic.ini` untuk lingkungan lain).
- **Framework**: Flask 3.1.1.
- **ORM/DB layer**: SQLAlchemy 2.0.40 dengan `scoped_session`, connection factory internal, dan migrasi via Alembic 1.15.2.
- **Storage utama**:
  - default development: `sqlite:///<BASE_DIR>/data.db`
  - production: `mysql+pymysql://` atau PostgreSQL (`postgresql+psycopg://` bila env menyediakan driver).
- **Excel processing**: pandas 3.0.1 + openpyxl 3.1.5.
- **Visualisasi**: plotly 6.5.0 (untuk chart data per indicator).

## Frontend Stack

- **Template engine**: Jinja2 (halaman server-side).
- **Styling**: Tailwind CSS + DaisyUI (build tooling di `assets/package.json` dan `assets/` static pipeline).
- **UI script**: vanilla JS dalam `templates/partials`, minimal ketergantungan frontend.

## Tooling

- **Testing**: pytest, Playwright (`@playwright/test`), skrip test custom.
- **Utility scripts**: `scripts/*.py` untuk maintenance/migrasi data (CLI), tidak dipanggil langsung oleh request web runtime.
- **Linting/format**: tidak ada linting config khusus di root saat ini.
- **Env loading**: python-dotenv (`load_dotenv`) dengan `DOTENV_PATH`.

## Deployment & Ops

- App default jalan di Flask host (preferensi preferensi user: host-based, MySQL via container).
- Dokumentasi operasi terpusat di `docs/README_DOCS.md` dan `SERVER_DEPLOYMENT.md`.
- Tidak ada CI pipeline terdeteksi dari scan.

## Runtime Dependencies (Ringkas)

- `config.py` memuat `.env`, memilih `DATABASE_URL`, mengatur `SESSION_COOKIE_*`, dan menerapkan proteksi produksi.
- `app.py` memakai application factory (`create_app`) dan guard produksi: `DATABASE_URL` wajib di `FLASK_ENV=production`.
- `wsgi.py` mengekspor `app` untuk server WSGI.

