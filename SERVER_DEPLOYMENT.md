# Panduan Deployment ke Server (via Webmin / Git, bukan GitHub UI)

Tujuan dokumen ini: deploy **webdash_neraca** ke server production/staging melalui terminal Webmin (atau shell SSH), inisialisasi DB, dan migrasi data dari SQLite ke MySQL.

Semua langkah menulis ke `.env` lokal di server (`.env` tidak di-commit).

## 1) Asumsi lingkungan

- Server Linux (Debian/Ubuntu) yang bisa diakses via **Webmin**.
- Tersedia `python3`, `git`, `mysql` client, `node` (kalau perlu build CSS), `systemd`.
- Aplikasi akan dijalankan di belakang reverse proxy (Nginx/Apache) dengan HTTPS.

## 2) Clone project langsung dari Git (tanpa GitHub UI)

1. Login Webmin → `Tools` → `Command Shell` (atau SSH).
2. Masuk ke folder aplikasi (contoh: `/var/www`).
3. Clone dari remote git internal/self-hosted:

```bash
cd /var/www
git clone ssh://git@internal.example.com:2222/team/webdash_neraca.git webdash_neraca
cd webdash_neraca
```

4. Pin dan checkout branch rilis:

```bash
git checkout main
```

5. (Opsional) tarik update:

```bash
git pull --ff-only
```

## 3) Setup Python + dependensi

```bash
cd /var/www/webdash_neraca
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Build aset frontend (kalau repo dipakai build-time)

```bash
npm install
npm run build:css
```

## 5) Buat `.env` production

1. Salin template.
2. Isi nilai sensitif dari secret manager/server vault (JANGAN commit).

```bash
cp .env.example .env
nano .env
```

Minimal yang wajib:

```env
FLASK_ENV=production
FLASK_RUN_PORT=5000
FLASK_SECRET_KEY=isi_dengan_secret_panjang
REQUIRE_FLASK_SECRET=1
SESSION_COOKIE_SECURE=1

MYSQL_TARGET_URL=mysql+pymysql://user_db:password_db@127.0.0.1:3306/webdash_neraca?charset=utf8mb4
DATABASE_URL=mysql+pymysql://user_db:password_db@127.0.0.1:3306/webdash_neraca?charset=utf8mb4
ALEMBIC_DATABASE_URL=mysql+pymysql://user_db:password_db@127.0.0.1:3306/webdash_neraca?charset=utf8mb4

SQLITE_SOURCE_PATH=/var/backups/webdash_neraca/data.db   # hanya dipakai saat migrasi
```

> Catatan: `DATABASE_URL` adalah DSN utama runtime Flask.

## 6) Inisialisasi MySQL dari awal (kalau DB/tabel belum ada)

### 6.1 Cek & buat DB serta user

```bash
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS webdash_neraca CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -uroot -p -e "CREATE USER IF NOT EXISTS 'webdash_user'@'127.0.0.1' IDENTIFIED BY 'ganti_password_kuat';"
mysql -uroot -p -e "GRANT ALL PRIVILEGES ON webdash_neraca.* TO 'webdash_user'@'127.0.0.1';"
mysql -uroot -p -e "FLUSH PRIVILEGES;"
```

### 6.2 Cek apakah tabel sudah ada

```bash
mysql -uwebdash_user -pganti_password_kuat -h 127.0.0.1 webdash_neraca -e "SHOW TABLES;"
```

- Jika hasilnya **kosong**, lanjut ke migrasi skema.
- Jika ada setengah jalan, lakukan backup dulu baru refresh.

### 6.3 Terapkan migrasi skema

```bash
source .venv/bin/activate
cd /var/www/webdash_neraca
export DATABASE_URL="$(grep '^DATABASE_URL=' .env | cut -d= -f2-)"
python -m alembic upgrade head
```

Verifikasi:

```bash
mysql -uwebdash_user -pganti_password_kuat -h 127.0.0.1 webdash_neraca -e "SHOW TABLES;"
```

Pastikan ada minimal `data_entries` dan `aggregated_summary`.

## 7) Migrasi dari SQLite ke MySQL di server

Gunakan ketika masih ada `data.db` lokal (legacy) yang ingin dipindah.

1. Salin file sumber SQLite ke server (contoh: `/var/backups/webdash_neraca/data.db`).
2. Validasi read-only (dry-run):

```bash
source .venv/bin/activate
cd /var/www/webdash_neraca
export SQLITE_SOURCE_PATH=/var/backups/webdash_neraca/data.db
export MYSQL_TARGET_URL="$DATABASE_URL"
python scripts/migrate_sqlite_to_mysql.py --dry-run
```

3. Kalau hasil cocok, migrasi penuh (full replace target):

```bash
python scripts/migrate_sqlite_to_mysql.py --truncate-target
```

4. Validasi pasca-migrasi:

```bash
mysql -uwebdash_user -pganti_password_kuat -h 127.0.0.1 webdash_neraca -e "SELECT COUNT(*) FROM data_entries; SELECT COUNT(*) FROM aggregated_summary;"
```

5. Jaga backup lama (sebelum truncate/migrate):

```bash
cp /var/backups/webdash_neraca/data.db /var/backups/webdash_neraca/data.db.$(date +%F_%H%M%S)
```

## 8) Cek cepat koneksi runtime (sebelum service aktif)

```bash
source .venv/bin/activate
python -c "from app import app; from models import get_total_entries_count; from infrastructure.db import engine_dialect_name; print(engine_dialect_name()); print('rows=', get_total_entries_count())"
```

Jalankan uji HTTP lokal:

```bash
python -m flask run --host=0.0.0.0 --port=5000
# di terminal lain:
curl -I http://127.0.0.1:5000/
curl -s http://127.0.0.1:5000/preview-data | head
```

Jika sudah benar, stop proses `flask run` dan lanjut service.

## 9) Jalankan dengan Gunicorn + systemd (produksi)

Buat `/etc/systemd/system/webdash.service`:

```ini
[Unit]
Description=Webdash Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/webdash_neraca
EnvironmentFile=/var/www/webdash_neraca/.env
ExecStart=/var/www/webdash_neraca/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable & start:

```bash
systemctl daemon-reload
systemctl enable --now webdash.service
systemctl status webdash.service
```

## 10) Reverse proxy di Webmin (Nginx/Apache)

Di Webmin, arahkan domain/subdomain ke `http://127.0.0.1:5000` lalu pasang sertifikat TLS.

## 11) Backup & restore operasional

- Backup DB:

```bash
mysqldump -uwebdash_user -pganti_password_kuat webdash_neraca > /var/backups/webdash_neraca/webdash_neraca_$(date +%F).sql
```

- Backup upload:

```bash
tar -czf /var/backups/webdash_neraca/uploads_$(date +%F).tar.gz /var/www/webdash_neraca/uploads
```

- Restore:

```bash
mysql -uwebdash_user -pganti_password_kuat webdash_neraca < /var/backups/webdash_neraca/webdash_neraca_YYYY-MM-DD.sql
tar -xzf /var/backups/webdash_neraca/uploads_YYYY-MM-DD.tar.gz -C /var/www/webdash_neraca
```

## 12) Checklist go-live

- [ ] `.env` sudah diisi dari secret manager (tidak disimpan di git).
- [ ] MySQL terpasang dan dapat diakses dari service user `www-data`.
- [ ] `python -m alembic upgrade head` sukses.
- [ ] `migrasi SQLite→MySQL` selesai dan `SELECT COUNT(*)` sesuai target.
- [ ] Service `webdash.service` aktif (systemd).
- [ ] Reverse proxy + HTTPS aktif.
- [ ] `/` dan `/preview-data` bisa diakses lewat domain publik.
- [ ] Pengujian upload satu file sample + generate chart/analysis sukses.

## 13) Troubleshooting cepat

- `Unknown database 'webdash_neraca'`  
  -> Cek `CREATE DATABASE` dan `DATABASE_URL` di `.env`.
- `Access denied`  
  -> Cek user/host/password MySQL dan firewall bind-address.
- `Migration fails: Target already has rows`  
 -> Gunakan `--truncate-target` saat full replace, atau migrasi ke DB kosong.
- `No module named PyMySQL`  
 -> Pastikan `pip install -r requirements.txt` di environment yang dipakai service.
- `Tables not found`  
 -> Jalankan `python -m alembic upgrade head` lagi setelah cek `.env`.

