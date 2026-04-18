# Panduan Deployment ke Server (via Webmin di Linux kantor)

Tujuan dokumen ini: deploy **webdash_neraca_v2** ke server kantor Linux melalui terminal Webmin (atau SSH), inisialisasi DB, dan migrasi data dari SQLite ke MySQL.

Semua langkah menulis ke `.env` lokal di server (`.env` tidak di-commit).

## 1) Asumsi lingkungan

- Server Linux (Debian/Ubuntu) yang bisa diakses via **Webmin**.
- **Catatan deployment:** container `docker-compose` di repo dipakai untuk **testing lokal laptop**, bukan pola deploy di server kantor.

## 1.1) Arsitektur testing lokal vs server kantor

- **Server kantor (Webmin/production):** pakai instalasi sistem langsung + `systemd` + reverse proxy.
- **Laptop pribadi:** pakai `docker-compose.mysql.yml` untuk simulasi cepat dan validasi fitur.
- Tersedia `python3`, `git`, `mysql` client, `node` (kalau perlu build CSS), `systemd`.
- Aplikasi akan dijalankan di belakang reverse proxy (Nginx/Apache) dengan HTTPS.

## 2) Clone project langsung dari Git (tanpa GitHub UI)

1. Login Webmin → `Tools` → `Command Shell` (atau SSH).
2. Masuk ke folder aplikasi (contoh: `/var/www`).
3. Clone dari remote git internal/self-hosted:

```bash
cd /var/www
git clone ssh://git@internal.example.com:2222/team/webdash_neraca_v2.git webdash_neraca_v2
cd webdash_neraca_v2
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
cd /var/www/webdash_neraca_v2
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

MYSQL_TARGET_URL=mysql+pymysql://user_db:password_db@127.0.0.1:3306/webdash_neraca_v2?charset=utf8mb4
DATABASE_URL=mysql+pymysql://user_db:password_db@127.0.0.1:3306/webdash_neraca_v2?charset=utf8mb4
ALEMBIC_DATABASE_URL=mysql+pymysql://user_db:password_db@127.0.0.1:3306/webdash_neraca_v2?charset=utf8mb4

SQLITE_SOURCE_PATH=/var/backups/webdash_neraca_v2/data.db   # hanya dipakai saat migrasi
```

> Catatan: `DATABASE_URL` adalah DSN utama runtime Flask.

### Mode koneksi DB (praktis)

- **Production kantor (Webmin):** set `DATABASE_URL` ke MySQL (`mysql+pymysql://...`), isi variabel user/password khusus service.
- **Fallback lokal / operasi backup sementara:** set `DATABASE_URL=sqlite:////var/backups/webdash_neraca_v2/data.db` untuk verifikasi cepat atau pemulihan darurat.
- **Tip:** `SQLITE_SOURCE_PATH` hanya dipakai saat migrasi, tidak dipakai sebagai source runtime normal.

## 6) Inisialisasi MySQL dari awal (kalau DB/tabel belum ada)

### 6.1 Cek & buat DB serta user

```bash
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS webdash_neraca_v2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -uroot -p -e "CREATE USER IF NOT EXISTS 'webdash_user'@'127.0.0.1' IDENTIFIED BY 'ganti_password_kuat';"
mysql -uroot -p -e "GRANT ALL PRIVILEGES ON webdash_neraca_v2.* TO 'webdash_user'@'127.0.0.1';"
mysql -uroot -p -e "FLUSH PRIVILEGES;"
```

### 6.2 Cek apakah tabel sudah ada

```bash
mysql -uwebdash_user -pganti_password_kuat -h 127.0.0.1 webdash_neraca_v2 -e "SHOW TABLES;"
```

- Jika hasilnya **kosong**, lanjut ke migrasi skema.
- Jika ada setengah jalan, lakukan backup dulu baru refresh.

### 6.3 Terapkan migrasi skema

```bash
source .venv/bin/activate
cd /var/www/webdash_neraca_v2
export DATABASE_URL="$(grep '^DATABASE_URL=' .env | cut -d= -f2-)"
python -m alembic upgrade head
```

Verifikasi:

```bash
mysql -uwebdash_user -pganti_password_kuat -h 127.0.0.1 webdash_neraca_v2 -e "SHOW TABLES;"
```

Pastikan ada `data_entries`.

## 7) Migrasi dari SQLite ke MySQL di server

Gunakan ketika masih ada `data.db` lokal (legacy) yang ingin dipindah.

1. Salin file sumber SQLite ke server (contoh: `/var/backups/webdash_neraca_v2/data.db`).
2. Validasi read-only (dry-run):

```bash
source .venv/bin/activate
cd /var/www/webdash_neraca_v2
export SQLITE_SOURCE_PATH=/var/backups/webdash_neraca_v2/data.db
export MYSQL_TARGET_URL="$DATABASE_URL"
python scripts/migrate_sqlite_to_mysql.py --dry-run
```

3. Kalau hasil cocok, migrasi penuh (full replace target):

```bash
python scripts/migrate_sqlite_to_mysql.py --truncate-target
```

4. Validasi pasca-migrasi:

```bash
mysql -uwebdash_user -pganti_password_kuat -h 127.0.0.1 webdash_neraca_v2 -e "SELECT COUNT(*) FROM data_entries;"
```

5. Jaga backup lama (sebelum truncate/migrate):

```bash
cp /var/backups/webdash_neraca_v2/data.db /var/backups/webdash_neraca_v2/data.db.$(date +%F_%H%M%S)
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

Buat `/etc/systemd/system/webdash_neraca_v2.service`:

```ini
[Unit]
Description=webdash_neraca_v2 Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/webdash_neraca_v2
EnvironmentFile=/var/www/webdash_neraca_v2/.env
ExecStart=/var/www/webdash_neraca_v2/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable & start:

```bash
systemctl daemon-reload
systemctl enable --now webdash_neraca_v2.service
systemctl status webdash_neraca_v2.service
```

## 10) Reverse proxy di Webmin (Nginx/Apache)

Di Webmin, arahkan domain/subdomain ke `http://127.0.0.1:5000` lalu pasang sertifikat TLS.

## 11) Backup & restore operasional (Webmin server kantor)

- Backup MySQL:

```bash
mysqldump -uwebdash_user -pganti_password_kuat webdash_neraca_v2 > /var/backups/webdash_neraca_v2/webdash_neraca_v2_$(date +%F).sql
```

- Backup direktori upload:

```bash
tar -czf /var/backups/webdash_neraca_v2/uploads_$(date +%F).tar.gz /var/www/webdash_neraca_v2/uploads
```

- Backup MySQL ke SQLite (opsional, untuk audit/restore lokal):

```bash
cd /var/www/webdash_neraca_v2
source .venv/bin/activate

# satu jalur default timestamped di /var/www/webdash_neraca_v2/backups
python scripts/migrate_mysql_to_sqlite.py
# contoh backup SQLite dari hasil konversi
ls -lh /var/www/webdash_neraca_v2/backups/*.db || true

# target file tetap untuk cron backup harian
export SQLITE_BACKUP_PATH=/var/backups/webdash_neraca_v2/webdash_data_backup.db
python scripts/migrate_mysql_to_sqlite.py --truncate-target

# preview dulu
python scripts/migrate_mysql_to_sqlite.py --truncate-target --dry-run
```

- Restore MySQL:

```bash
mysql -uwebdash_user -pganti_password_kuat webdash_neraca_v2 < /var/backups/webdash_neraca_v2/webdash_neraca_v2_YYYY-MM-DD.sql
tar -xzf /var/backups/webdash_neraca_v2/uploads_YYYY-MM-DD.tar.gz -C /var/www/webdash_neraca_v2
```

### 11.1 Backup SQLite (jika dipakai untuk debug/arsip)

Jika menggunakan SQLite untuk analisis lokal atau backup ringan:

```bash
cp /var/backups/webdash_neraca_v2/data.db /var/backups/webdash_neraca_v2/data.db.$(date +%F_%H%M%S)
sqlite3 /var/backups/webdash_neraca_v2/data.db "PRAGMA integrity_check;"
```

Restore SQLite dari backup:

```bash
cp /var/backups/webdash_neraca_v2/data.db.YYYY-MM-DD_HHMMSS /var/backups/webdash_neraca_v2/data.db
```

## 12) Checklist go-live

- [ ] `.env` sudah diisi dari secret manager (tidak disimpan di git).
- [ ] MySQL terpasang dan dapat diakses dari service user `www-data`.
- [ ] `python -m alembic upgrade head` sukses.
- [ ] `migrasi SQLite→MySQL` selesai dan `SELECT COUNT(*)` sesuai target.
- [ ] Service `webdash_neraca_v2.service` aktif (systemd).
- [ ] Reverse proxy + HTTPS aktif.
- [ ] `/` dan `/preview-data` bisa diakses lewat domain publik.
- [ ] Pengujian upload satu file sample + generate chart/analysis sukses.

## 13) Troubleshooting cepat

- `Unknown database 'webdash_neraca_v2'`  
  -> Cek `CREATE DATABASE` dan `DATABASE_URL` di `.env`.
- `Access denied`  
  -> Cek user/host/password MySQL dan firewall bind-address.
- `Migration fails: Target already has rows`  
 -> Gunakan `--truncate-target` saat full replace, atau migrasi ke DB kosong.
- `No module named PyMySQL`  
 -> Pastikan `pip install -r requirements.txt` di environment yang dipakai service.
- `Tables not found`  
 -> Jalankan `python -m alembic upgrade head` lagi setelah cek `.env`.
- `docker compose` di production gagal terhubung
  -> Normal jika kamu deploy via systemd. Pastikan perintah di checklist server kantor memakai service/systemd + konfigurasi Webmin, bukan container local.

