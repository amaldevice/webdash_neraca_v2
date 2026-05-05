# Project Feature Tracking

## Current Feature Set
- **Landing dashboard**: Metrik repository menampilkan ringkasan ringkas, metadata (uploader, version), dengan aksi cepat ke unggah, manual input, atau dashboard analisis.
- **Dual ingestion routes**: Users can upload Excel files (horizontal or vertical templates) or manually enter indicators; both flows share metadata validation (uploader, version, data type, period) and normalization helpers before persisting to SQLite.
- **Planning synchronization**: Every code change documented in `planning.md` and the cursor plan per the project rule, keeping implementation status aligned with the documentation.
- **Dashboard table + filters**: Filter persisted entries by data type and time period, display the latest rows, dan metrik dihitung langsung dari data aktif.
- **Raw exports**: Export the filtered rows directly as CSV or Excel straight from the dashboard filters.

## Feature Change Log

### Latest State (after current round of work)
- **Aggregation cache + summary refresh**: Dihapus. Setiap insert langsung memperbarui data sumber tanpa cache agregat; landing/dashboard membaca data aktif.
- **Validation layer**: Upload/manual forms now check `data_type` and `time_period` against allowed values before inserting data, ensuring consistent metadata for downstream analytics.
- **Export links**: Added `/export` route with CSV and Excel options that stream the same filtered rows shown on the dashboard, giving analysts access to raw repository data.
- **Planning sync rule**: Introduced `.cursor/rules/planning-sync.mdc` so contributors always update `planning.md` and the cursor plan alongside any code change.
- **Simple Testing Suite**: Comprehensive testing framework created with functional tests (61 passed), security testing (68 vulnerabilities identified), and UI testing framework (MCP dependency issue noted).

### Previous Snapshot (before latest changes)
- **Excel parser + normalization**: Handler identified layout type, normalized rows into the shared schema, and stored uploader/version metadata plus derived year/month/quarter values.
- **Manual ingestion**: Form allowed quick data entry with metadata, reusing the same persistence helpers as the Excel flow.
- **Landing + repository views**: Initial dashboards rendered repository metrics and placeholder tables before filtering/export functionality matured.
