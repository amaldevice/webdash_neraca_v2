# QA Checklist

Use this checklist for manual verification after changes.

## Setup
- [ ] Start the app (`python app.py`).
- [ ] Confirm landing page loads at `/`.

## Upload Excel
- [ ] Upload a valid `.xlsx` file via `/upload`.
- [ ] Verify success flash message and entry count increases.
- [ ] Upload an invalid file type and confirm validation error.

## Manual Input
- [ ] Submit a manual entry via `/manual` with valid metadata and value.
- [ ] Verify success message and entry appears in preview.
- [ ] Submit with missing fields and confirm validation error.

## Aggregated Summary
- [ ] Visit `/aggregated` and confirm cards render.
- [ ] Filter by indicator and confirm plot filter list is populated.

## Preview & Pagination
- [ ] Visit `/preview-data` and verify rows render.
- [ ] Change `limit` to 10/20/50 and confirm pagination updates.
- [ ] Apply filters (data type, time period, uploader, indicator) and verify results.

## Export
- [ ] Export CSV (`/export?format=csv`) and verify file contents.
- [ ] Export Excel (`/export?format=excel`) and verify file opens.

## Data Management (CRUD)
- [ ] Insert a row via `/data-management` and confirm it appears.
- [ ] Update a row and confirm changes persist.
- [ ] Delete a single row and confirm removal.
- [ ] Delete by filter and confirm only filtered rows are removed.

## Plot
- [ ] On `/aggregated`, select an indicator and generate a plot.
- [ ] Confirm plot renders with data.
- [ ] Try with an indicator that has no data and confirm error message.
