## Parent

Refactor — Dead Code Removal & upload_flow.py Decomposition (PRD: `docs/plans/refactor-dead-code-decomposition.md`)

## What to build

Remove the legacy raw SQL code path that has been fully replaced by the SQLAlchemy-based implementation. This includes two functions that build raw SQL string clauses — neither has any caller in the active codebase.

Delete `_build_data_entry_filter_clauses()` from the data filters module and `apply_period_range_filter()` from the period filters module. Clean up any imports that reference these functions. Run the full test suite to confirm zero regression.

## Acceptance criteria

- [ ] `_build_data_entry_filter_clauses()` is removed from the codebase
- [ ] `apply_period_range_filter()` is removed from the codebase
- [ ] No remaining imports reference either function
- [ ] `pytest` passes with zero failures
- [ ] The SQLAlchemy-based filter builders (`build_data_entry_filter_sqlalchemy`, `build_period_range_filter_sqlalchemy`) remain intact and functional

## Blocked by

None — can start immediately.
