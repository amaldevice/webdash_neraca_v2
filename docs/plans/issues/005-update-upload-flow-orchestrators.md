## Parent

Refactor — Dead Code Removal & upload_flow.py Decomposition (PRD: `docs/plans/refactor-dead-code-decomposition.md`)

## What to build

Update `services/upload_flow.py` to serve as the thin orchestrator module after decomposition. This file retains the 3 top-level orchestrators, 2 response dataclasses, and the shared parsing/validation function — everything routes actually import.

Verify the final state:
- `upload_flow.py` contains: `UploadFlowResponse`, `ManualFlowResponse`, `build_upload_response`, `upload_folder_from_config`, `parse_and_validate_upload_payload`, `process_upload_confirm`, `process_upload_post_file`, `process_manual_input_post`
- All other functions have been moved to `upload_form.py`, `upload_duplicates.py`, or `upload_handlers.py`
- Imports are clean and reference the new modules
- Public API is unchanged (routes don't need modification)
- Dependency direction: `upload_flow` → `upload_handlers` → `upload_duplicates` → `upload_form`

Run the full test suite to confirm the decomposition is complete and correct.

## Acceptance criteria

- [ ] `services/upload_flow.py` is reduced to ~370 lines (from 1023)
- [ ] All functions not listed above have been moved to the appropriate new modules
- [ ] `upload_flow.py` imports from `upload_form`, `upload_duplicates`, and `upload_handlers`
- [ ] No dead imports remain in `upload_flow.py`
- [ ] `routes/upload_routes.py` requires no changes
- [ ] `pytest` passes with zero failures
- [ ] `docs/plans/refactor-dead-code-decomposition.md` is updated to reflect completed status

## Blocked by

- #22 (upload_form.py must exist)
- #23 (upload_duplicates.py must exist)
- #24 (upload_handlers.py must exist)
