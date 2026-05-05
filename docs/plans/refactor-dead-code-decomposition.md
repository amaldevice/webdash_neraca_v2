# PRD: Refactor — Dead Code Removal & upload_flow.py Decomposition

## Problem Statement

Codebase `webdash_neraca_v2` memiliki dua masalah utama yang menghambat maintainability:

1. **Dead code / legacy code path** — Terdapat raw SQL code path (`_build_data_entry_filter_clauses` di `models/data_filters.py` dan `apply_period_range_filter` di `services/period_filters.py`) yang sudah digantikan oleh SQLAlchemy-based code path. Kedua fungsi ini tidak memiliki caller di active code, namun tetap memakan maintenance burden dan membingungkan developer baru.

2. **Monolith file** — `services/upload_flow.py` (1023 baris) memiliki 5 responsibility berbeda yang tercampur dalam satu file: form parsing, duplicate detection, branch handlers, persistence, dan orchestration. File ini adalah entry point utama untuk seluruh upload pipeline, sehingga setiap perubahan kecil memerlukan pemahaman keseluruhan file.

## Solution

### Phase 1: Dead Code Removal
Hapus legacy SQL code path yang sudah tidak terpakai:
- Hapus `_build_data_entry_filter_clauses()` dari `models/data_filters.py`
- Hapus `apply_period_range_filter()` dari `services/period_filters.py`
- Bersihkan import/export yang tidak diperlukan
- Verifikasi semua test masih pass

### Phase 2: upload_flow.py Decomposition (4-file split)
Pecah `upload_flow.py` menjadi 4 modul dengan responsibility terpisah:

| Modul | Responsibility | ~Lines |
|---|---|---|
| `services/upload_form.py` | Form parsing, validation, file save | ~70 |
| `services/upload_duplicates.py` | Duplicate detection, counting, resolution planning | ~110 |
| `services/upload_handlers.py` | Branch handlers (7 `handle_*`) + persistence wrappers | ~340 |
| `services/upload_flow.py` | Orchestrators + response types + config | ~370 |

Routes tidak berubah — tetap import dari `services.upload_flow`.

## User Stories

1. As a developer, I want legacy raw SQL code path dihapus, sehingga codebase hanya memiliki satu code path (SQLAlchemy) dan tidak membingungkan.
2. As a developer, I want `upload_flow.py` dipecah menjadi modul-modul kecil, sehingga saya bisa memahami satu responsibility tanpa membaca 1023 baris.
3. As a developer, I want form parsing logic terisolasi di `upload_form.py`, sehingga bisa di-unit-test tanpa DB mocking.
4. As a developer, I want duplicate detection logic terisolasi di `upload_duplicates.py`, sehingga bisa di-test secara independent.
5. As a developer, I want branch handlers terisolasi di `upload_handlers.py`, sehingga setiap branch bisa dipahami secara terpisah.
6. As a developer, I want orchestrators tetap di `upload_flow.py`, sehingga routes tidak perlu diubah.
7. As a developer, I want semua test pass setelah setiap phase refactor, sehingga tidak ada regression.
8. As a developer, I want dependency direction bersih (flow → handlers → duplicates → form), sehingga tidak ada circular import.

## Implementation Decisions

### Modul yang dihapus
- `models/data_filters.py`: hapus `_build_data_entry_filter_clauses()`, pertahankan `build_data_entry_filter_sqlalchemy()`
- `services/period_filters.py`: hapus `apply_period_range_filter()`, pertahankan SQLAlchemy-based filter builders

### Modul yang dibuat
- `services/upload_form.py`: berisi `parse_upload_form`, `collect_upload_file_errors`, `normalize_upload_action`, `_form_getlist`, `save_uploaded_excel`
- `services/upload_duplicates.py`: berisi `_collect_internal_duplicate_counts`, `_build_internal_duplicate_warning_message`, `_hydrate_duplicate_records_with_values`, `prepare_duplicate_plan`, `_build_duplicate_confirmation_summary`, `_duplicate_conflict_message`
- `services/upload_handlers.py`: berisi 7 `handle_*` functions, 2 `persist_*` wrappers, `_safe_remove_file`

### Modul yang diupdate
- `services/upload_flow.py`: update imports dari 3 modul baru, pertahankan public API yang sama

### Dependency direction
```
upload_flow.py (orchestrators)
    ↓
upload_handlers.py (branch logic)
    ↓
upload_duplicates.py (helpers)
    ↓
upload_form.py (pure input handling)
```

### Routes
`routes/upload_routes.py` tidak diubah — tetap import dari `services.upload_flow`.

## Testing Decisions

- Jalankan `pytest` setelah Phase 1 (dead code removal) untuk verifikasi zero regression
- Jalankan `pytest` setelah Phase 2 (decomposition) untuk verifikasi semua import benar
- Test existing sudah cover: `tests/test_upload_flow.py` (466 baris), `tests/test_upload_preview.py` (260 baris), `tests/test_bugs.py` (584 baris)
- Tidak perlu test baru untuk decomposition karena ini pure refactoring (behavior tidak berubah)

## Out of Scope

- XLSX files consolidation (pindah file .xlsx dari root ke tests/fixtures/)
- Dead code lain: `UPLOAD_PREVIEW_CACHE`, `_to_float` variants, `app.py` legacy aliases
- `upload_flow.py` internal restructuring (hanya split, tidak rewrite logic)
- CI/CD pipeline setup
- Linter/formatter configuration

## Further Notes

- Codebase menggunakan Flask 3.1.1, SQLAlchemy 2.0.40, Python 3.12+
- Database: SQLite (dev), MySQL/PostgreSQL (prod)
- Semua test harus pass sebelum merge
- Decomposition tidak mengubah behavior — pure structural refactor
