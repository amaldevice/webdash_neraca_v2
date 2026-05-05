## Parent

Refactor — Dead Code Removal & upload_flow.py Decomposition (PRD: `docs/plans/refactor-dead-code-decomposition.md`)

## What to build

Extract duplicate detection and resolution logic from `upload_flow.py` into a new `services/upload_duplicates.py` module. This module contains all duplicate-related helpers shared by both the upload-file and manual-entry flows.

Move these functions:
- `_collect_internal_duplicate_counts` — count intra-file duplicates by indicator+period
- `_build_internal_duplicate_warning_message` — format warning string from duplicate counts
- `_hydrate_duplicate_records_with_values` — enrich DB duplicate records with uploaded values
- `prepare_duplicate_plan` — build skip/overwrite plan from user selections
- `_build_duplicate_confirmation_summary` — summarize skipped/overwritten/safe row counts
- `_duplicate_conflict_message` — fixed Indonesian error message for DB conflict

Update `services/upload_flow.py` to import these functions from the new module. Public API remains unchanged.

## Acceptance criteria

- [ ] `services/upload_duplicates.py` exists with the 6 functions listed above
- [ ] `services/upload_flow.py` imports these functions from `upload_duplicates` instead of defining them locally
- [ ] `routes/upload_routes.py` requires no changes
- [ ] `pytest` passes with zero failures
- [ ] No circular imports between modules

## Blocked by

None — can start immediately.
