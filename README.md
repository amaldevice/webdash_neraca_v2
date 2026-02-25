# BPS Data System

> Minimal Flask + SQLite prototype to upload BPS Excel templates or manual entries, normalize them, cache aggregated summaries, and expose filtered dashboards + raw exports.

## Features

### Core Features
- [x] **Landing portal**: Aggregated cards, metadata, and quick actions for upload/manual/summary views.
- [x] **Dual ingestion paths**: Excel parser handles horizontal/vertical templates while manual input keeps metadata enforced.
- [x] **Aggregation & caching**: Aggregator layer stores pre-computed cards and metadata for landing/dashboard reuse.

### Additional Features
- [x] **Filtering table**: Dashboard filters by data type/period and renders the last 50 persisted entries.
- [x] **Raw exports**: Download filtered data as CSV or Excel before aggregation.
- [x] **Validation guardrails**: Metadata validation ensures uploader, version, data_type, and time_period remain consistent.

## Architecture

### High-Level Overview
Flask routes handle upload/manual ingestion → shared parser/normalizer → SQLite `data_entries` store + aggregation cache → aggregator fetches latest summary → templates render landing/dashboard/aggregated pages → export route streams raw rows.

### Component Diagram
```
Landing Page + Forms
    ↓ HTTP POST
Flask App (app.py)
    ↓ Parser/Model helpers
    ↓ SQLite (data_entries, aggregated_summary)
Aggregation Trigger (refresh_aggregated_summary) → cached summary
    ↓ HTTP GET
Dashboard / Aggregated Templates
```

### Data Flow
1. **User Action** → Upload Excel or fill manual form (metadata + data_type/time_period).
2. **Backend Processing** → Validation → parser/normalizer → insert into SQLite → trigger aggregation refresh.
3. **Response** → Updated widgets, filtered table, export links, and aggregated summaries.

### Key Workflows
#### Primary User Journey
1. User visits `/` to see latest summary, metadata, and action cards.
2. Upload Excel or enter manual record (both require uploader name + version + data meta).
3. App parses/normalizes data, persists rows, refreshes cache.
4. User visits `/dashboard` to filter by data_type/time_period and explore both cards and raw table.
5. Export filtered rows as CSV/Excel if needed.

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
- **Styling**: Custom CSS
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

## Getting Started

### Prerequisites
- Python 3.12+
- `pip` (comes with Python)
- Optional: virtual environment

### Installation
```bash
git clone <repo-url>
cd webdash_neraca
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Environment setup
No `.env` yet; configure `FLASK_SECRET_KEY` or `FLASK_RUN_PORT` via environment variables if needed.

### Database setup
```bash
python -c "from models import init_db; init_db()"
```

### Start development server
```bash
python app.py
```

### Environment Variables
```env
FLASK_SECRET_KEY=change-me-for-production
FLASK_RUN_PORT=5000
```

### Available scripts
This project uses plain Python, so run:
```bash
python app.py       # start server
pytest              # run unit tests
python -m py_compile app.py models.py excel_parser.py aggregator.py
```

## Usage

### Basic Usage
1. Visit `http://localhost:5000` for the landing page summary and metadata.
2. Upload Excel via `/upload` or manually post data at `/manual`.
3. Visit `/dashboard` to filter/table data and use export links.
4. `/aggregated` shows the cached aggregator view.

### API Usage
```bash
GET /dashboard?data_type=flow&time_period=monthly
GET /export?format=csv
GET /export?format=excel
```

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
