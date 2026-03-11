# BPS Data System

> Minimal Flask + SQLite prototype to upload BPS Excel templates or manual entries, normalize them, cache aggregated summaries, and expose filtered dashboards + raw exports.

## 1-3 Fast Setup

1. Clone repository dan masuk ke folder proyek.
2. Install dependencies memakai `pip` atau `uv pip`.
3. Jalankan inisialisasi database, lalu start aplikasi di `http://127.0.0.1:5000`.

## Installation (pip)

```bash
git clone <repo-url>
cd webdash_neraca
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -c "from models import init_db; init_db()"
npm install
npm run build:css
python app.py
```

## Installation (uv pip)

```bash
git clone <repo-url>
cd webdash_neraca
python -m pip install uv
uv venv .venv
.\.venv\Scripts\activate
uv pip install -r requirements.txt
python -c "from models import init_db; init_db()"
npm install
npm run build:css
python app.py
```

## Features

### Core Features
- [x] **Landing portal**: Aggregated cards, metadata, and quick actions for upload/manual/summary views.
- [x] **Dual ingestion paths**: Excel parser handles horizontal/vertical templates while manual input keeps metadata enforced.
- [x] **Aggregation & caching**: Aggregator layer stores pre-computed cards and metadata for landing and aggregated reuse.

### Additional Features
- [x] **Date-range filtering**: Preview-Data dan Data-Management memakai `start_period` + `end_period`; Aggregated memakai `period_start` + `period_end` (grafik) dan `period_start` + `end_period` (analisis periode).
- [x] **Filtered table browsing**: Pagination, limit selector, and consistent row/table rendering across halaman utama data.
- [x] **Raw exports**: Download filtered rows as CSV/Excel via `/export` dengan parameter filter yang tetap terjaga.
- [x] **Validation guardrails**: Metadata validation memastikan uploader, version, data_type, dan time_period tetap valid.
- [x] **Bulk actions**: Data-Management memiliki bulk update, bulk delete, dan pilihan delete by filter.
- [x] **Period analysis workflow**: Aggregated menyediakan analisis periode (M to M, Q to Q, Y to Y, YTD, C to C) dan export Excel hasil analisis.

### Feature Coverage yang sebelumnya belum tertulis
- ✅ `playwright_period_filter_smoke.spec.js` sebagai smoke test untuk verifikasi alur rentang periode.
- ✅ Konsistensi UI tombol, form, dan komponen tabel yang sudah disatukan antar halaman (preview + management).
- ✅ Penyimpanan state filter di URL untuk preview/data-management agar mudah dibagikan/reuse.
- ✅ Batas halaman (pagination) dan reset filter state otomatis untuk menjaga hasil filter tetap konsisten saat pindah halaman.

## Architecture

### High-Level Overview
Flask routes handle upload/manual ingestion → shared parser/normalizer → SQLite `data_entries` store + aggregation cache → aggregator refreshes summary → templates render landing, preview, data-management, and aggregated pages → exports/analysis routes stream raw data and computed analysis.

### Component Diagram
```
Landing Page + Forms
    ↓ HTTP POST
Flask App (app.py)
    ↓ Parser/Model helpers
    ↓ SQLite (data_entries, aggregated_summary)
Aggregation Trigger (refresh_aggregated_summary) → cached summary
    ↓ HTTP GET
Preview / Data-Management / Aggregated Templates
```

### Data Flow
1. **User Action** → Upload Excel or fill manual form (metadata + data_type/time_period).
2. **Backend Processing** → Validation → parser/normalizer → insert into SQLite → trigger aggregation refresh.
3. **Response** → Updated widgets, filtered table, export links, and aggregated summaries.

### Key Workflows
#### Primary User Journey
1. User opens `/` to see latest summary, metadata, and shortcut actions.
2. Upload Excel or input manual record (both require uploader name + version + data metadata).
3. App parses/normalizes, stores rows, then refreshes cached summary.
4. User explores:
   - `/preview-data` untuk melihat tabel data + filter, dengan opsi rentang periode.
   - `/data-management` untuk maintenance data + bulk actions.
   - `/aggregated` untuk view agregat dan analisis periodik.
5. Semua filter relevan (termasuk `start_period`/`end_period`) ikut dipakai saat ekspor maupun analisis.

#### Secondary Workflows
- `/aggregated` shows cached summary + metadata timestamp.
- `/export` streams raw CSV/Excel for analysts before aggregation.

## Database Schema

### Core Tables
- **data_entries**: Persists uploader metadata, normalize time breakdown, data_type/period, indicator, value.
- **aggregated_summary**: Cache for latest summary JSON + timestamp.

### Relationships
```
data_entries (N) → aggregated_summary (1 cached snapshot per refresh)
```

## Tech Stack

### Frontend
- **Templating**: Jinja2
- **Styling**: Tailwind CSS + DaisyUI (CLI build) + minimal custom CSS
- **Asset delivery**: Flask static serving (CSS + JS placeholders)

### Backend
- **Runtime**: Python 3.12+
- **Framework**: Flask 3.1
- **Database**: SQLite
- **Excel Processing**: pandas + openpyxl
- **ORM/Helpers**: Plain `sqlite3` wrappers + helper functions
- **Validation**: Custom Python functions + flash messaging

### DevOps & Tools
- **Version Control**: Git
- **Documentation**: Markdown plans + README
- **Testing**: `python -m py_compile` syntax checks

### Environment Variables
```env
FLASK_SECRET_KEY=change-me-for-production
FLASK_RUN_PORT=5000
```

## Active Endpoints
```bash
GET  /               # landing + summary
GET,POST /upload     # upload Excel
GET,POST /manual     # input manual
GET  /preview-data   # tabel pratinjau + filter/export
GET,POST /data-management # manage data + bulk action
GET  /aggregated     # summary agregat + plot/analisis
GET  /export         # export CSV / Excel (mendukung filter aktif)
POST /generate-plot  # generate grafik garis berdasarkan indikator + rentang periode
POST /generate-period-analysis # generate analisis periode
POST /export-period-analysis # export hasil analisis ke Excel
```

### Available scripts
This project uses plain Python, so run:
```bash
python app.py       # start server
pytest              # run unit tests
python -m py_compile app.py models.py excel_parser.py aggregator.py

# Frontend assets
npm run build:css
```
## Usage

### Basic Usage
1. Visit `http://localhost:5000` for the landing page summary and metadata.
2. Upload Excel via `/upload` or manually post data at `/manual`.
3. Use `/preview-data` untuk filter dan ekspor data mentah.
4. Use `/data-management` untuk kelola data, bulk update, dan delete.
5. Use `/aggregated` untuk visualisasi + analisis rentang periode.

### API Usage
```bash
GET /preview-data?data_type=flow&time_period=monthly&start_period=2024&end_period=2024-Q4&limit=20&page=1
GET /data-management?time_period=quarterly&start_period=2024-Q1&end_period=2024-Q4
GET /export?format=csv&data_type=flow&start_period=2024&end_period=2024-Q4
GET /export?format=excel&start_period=2024&end_period=2024-Q4
POST /generate-plot (form: indicator=..., period_start=2024, period_end=2024-Q4, ...)
POST /generate-period-analysis (form: period_start=2024, end_period=2024-Q4, comparison_type=year-over-year)
POST /export-period-analysis (form: period_start=2024, end_period=2024-Q4)
```

### Cara cek fitur rentang periode
1. **Preview-Data**
   - Buka `/preview-data`.
   - Isi `Rentang Periode Mulai` dan `Rentang Periode Akhir`, klik `Terapkan Filter`.
   - Pastikan URL berubah dengan `start_period` + `end_period`, lalu klik export CSV/Excel → file mengikuti filter ini.
2. **Data-Management**
   - Buka `/data-management`.
   - Isi field periode, submit filter, lalu verifikasi tombol aksi (`Hapus Berdasarkan Filter`) muncul sesuai kondisi.
3. **Aggregated**
   - Buka `/aggregated`.
   - Isi `Periode Mulai` / `Periode Akhir` pada form plot dan klik `Hasilkan Grafik Garis`; cek payload request mengandung `period_start` dan `end_period`.
   - Pada `Analisis Periode`, isi `Rentang Periode` lalu klik `Hasilkan Analisis Periode`; pastikan hasil dan export analisis juga memakai rentang yang sama.

## Development Guidelines

### Code Style
- Keep Python code ≤ 120 columns.
- Prefer descriptive helpers (`models.py`, `excel_parser.py`, etc.).
- Document new routes/templates with inline comments where needed.

### Git Workflow
```bash
git checkout -b feature/<name>
# make changes
git add .
git commit -m "feat: describe change"
git push origin feature/<name>
```

### Testing Strategy
- Run unit tests: `pytest`.
- Run `python -m py_compile ...` after structural changes.
- Manual smoke test by exercising upload/manual flows (see `QA_CHECKLIST.md`).
- Untuk rentang periode, jalankan: `npx playwright test simple_tests/ui_tests/playwright_period_filter_smoke.spec.js`.

## Deployment

### Production Requirements
- Python 3.13+ runtime (with Flask, pandas, openpyxl) on server.
- Filesystem writable for `uploads/` and `data.db`.
- Configure `FLASK_SECRET_KEY` for session security.

### Deployment Steps
1. Prepare server with Python dependencies.
2. Copy `.db` and `uploads/` directories (or use migration strategy).
3. Set environment vars (`FLASK_SECRET_KEY`, `FLASK_RUN_PORT`).
4. Run `python app.py` behind a reverse proxy (e.g., Gunicorn + Nginx).

## Roadmap & Future Enhancements

### Short Term
- [ ] Add authentication + audit trails for uploads.
- [ ] Improve error states + loading indicators.
- [ ] Add PDF export + direct Excel template templates.

### Medium Term
- [ ] Add scheduled aggregation refresh + data lake sync.
- [ ] Implement multi-language support (i18n).
- [ ] Introduce API versioning and request throttling.

### Long Term
- [ ] Scale via microservices or worker queues.
- [ ] Add AI signatures for anomaly detection.
- [ ] Connect to BPS production dashboards or data lakes.

## Contributing & Support

### How to Contribute
1. Fork repository.
2. Create feature branch.
3. Write code + tests.
4. Run lint/test commands.
5. Submit PR for review.

### Support
- Documentation: this README + `planning.md`.
- Questions: open GitHub Issues.

## License
MIT License.
