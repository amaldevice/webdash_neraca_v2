# Upload: `data_entries` vs `upload_runs` transactions

## Domain

- **`data_entries`**: normalized facts (indicator, period, value, uploader, version, `dataset_code`, …).
- **`upload_runs`**: lightweight audit trail (status, `row_count`, `file_name`, timestamps) — implementation: `services/upload_runs.py`.

## Transaction boundaries (current code)

- Rows are written to `data_entries` inside `write_session` / `scoped_transaction` via `insert_entries` / `upsert_entries` (`models/mutations.py` → `services/upload_commit.py`). That block commits (or rolls back) as one unit.
- `record_upload_run` opens a **separate** `scoped_transaction`, inserts one `UploadRun`, commits independently. Failures there are logged and swallowed so uploads still succeed.

## Ordering

- On success paths, handlers persist `data_entries` first, then call `record_upload_run`. There is **no single atomic transaction** spanning both tables.

## Trade-off

- **Pro:** Audit/logging cannot block the primary user-facing commit; partial DB issues on `upload_runs` do not stop ingestion.
- **Con:** Possible state: rows in `data_entries` without a matching `upload_runs` row if the audit insert fails after the data transaction commits.

Stricter atomicity would require one shared SQLAlchemy session/transaction and an explicit error policy (different product contract).

Related: GitHub issue #68; code paths `services/upload_handlers.py`, `services/upload_runs.py`, `models/mutations.py`.
