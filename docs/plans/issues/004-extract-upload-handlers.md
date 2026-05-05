## Parent

Refactor — Dead Code Removal & upload_flow.py Decomposition (PRD: `docs/plans/refactor-dead-code-decomposition.md`)

## What to build

Extract branch handlers and persistence wrappers from `upload_flow.py` into a new `services/upload_handlers.py` module. Each handler implements one specific branch of the upload flow (e.g., confirm-with-duplicates, save-without-duplicates, preview).

Move these functions:
- `handle_upload_confirm_with_duplicates` — confirm flow when DB duplicates exist (107 lines)
- `handle_upload_confirm_without_duplicates` — confirm flow when no DB duplicates (41 lines)
- `handle_upload_post_file_no_entries` — empty file handler (19 lines)
- `handle_upload_post_file_save_with_duplicates` — save + duplicates → preview session (40 lines)
- `handle_upload_post_file_save_without_duplicates` — save, no duplicates → immediate persist (42 lines)
- `handle_upload_post_file_preview` — cache payload for preview (49 lines)
- `persist_upload_entries` — plain insert wrapper (6 lines)
- `persist_upload_entries_with_overwrite` — upsert wrapper (6 lines)
- `_safe_remove_file` — file cleanup with retry (13 lines)

Update `services/upload_flow.py` to import these functions from the new module. Public API remains unchanged.

## Acceptance criteria

- [ ] `services/upload_handlers.py` exists with the 9 functions listed above
- [ ] `services/upload_flow.py` imports these functions from `upload_handlers` instead of defining them locally
- [ ] `routes/upload_routes.py` requires no changes
- [ ] `pytest` passes with zero failures
- [ ] No circular imports between modules
- [ ] Dependency direction is clean: `upload_flow` → `upload_handlers` → `upload_duplicates` → `upload_form`

## Blocked by

- #22 (upload_form.py must exist before handlers can import from it)
- #23 (upload_duplicates.py must exist before handlers can import from it)
