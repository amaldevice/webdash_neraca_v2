## Parent

Refactor — Dead Code Removal & upload_flow.py Decomposition (PRD: `docs/plans/refactor-dead-code-decomposition.md`)

## What to build

Extract form parsing and validation logic from `upload_flow.py` into a new `services/upload_form.py` module. This module handles pure input processing with no DB access or file I/O side effects (except `save_uploaded_excel` which writes the uploaded file to disk).

Move these functions:
- `parse_upload_form` — extract form fields from POST request
- `collect_upload_file_errors` — validate required fields and attached file
- `normalize_upload_action` — coerce action string to allowed values
- `_form_getlist` — normalize multi-value form field extraction
- `save_uploaded_excel` — persist uploaded file to disk with UUID name

Update `services/upload_flow.py` to import these functions from the new module. Public API remains unchanged — routes continue importing from `services.upload_flow`.

## Acceptance criteria

- [ ] `services/upload_form.py` exists with the 5 functions listed above
- [ ] `services/upload_flow.py` imports these functions from `upload_form` instead of defining them locally
- [ ] `routes/upload_routes.py` requires no changes
- [ ] `pytest` passes with zero failures
- [ ] No circular imports between modules

## Blocked by

None — can start immediately.
