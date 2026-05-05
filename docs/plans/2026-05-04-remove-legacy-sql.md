# Remove Legacy SQL Code Path Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove unused legacy SQL code path functions `_build_data_entry_filter_clauses` and `apply_period_range_filter` from the codebase.

**Architecture:** Delete two functions that are no longer called by any active code. The SQLAlchemy-based replacements (`build_data_entry_filter_sqlalchemy` and `period_analysis_range_sqlalchemy`) remain untouched.

**Tech Stack:** Python, SQLAlchemy

---

### Task 1: Remove `_build_data_entry_filter_clauses` from `models/data_filters.py`

**Files:**
- Modify: `models/data_filters.py:9` (import line)
- Modify: `models/data_filters.py:17` (docstring reference)
- Modify: `models/data_filters.py:37-82` (function definition)

**Step 1: Remove the import of `apply_period_range_filter` from line 9**

Change line 9 from:
```python
from services.period_filters import apply_period_range_filter, parse_period_filter_value, period_index
```
To:
```python
from services.period_filters import parse_period_filter_value, period_index
```

**Step 2: Update docstring on line 17**

Change line 17 from:
```python
    Matches ``apply_period_range_filter`` with ``time_period_filter`` falsy.
```
To:
```python
    Used when ``time_period_filter`` is falsy (analysis / mixed periods).
```

**Step 3: Delete the `_build_data_entry_filter_clauses` function (lines 37-82)**

Remove the entire function definition and its body.

**Step 4: Verify file integrity**

Run: `python -c "import ast; ast.parse(open('models/data_filters.py').read()); print('Syntax OK')"`
Expected: `Syntax OK`

---

### Task 2: Clean up `models/__init__.py`

**Files:**
- Modify: `models/__init__.py:9` (import line)
- Modify: `models/__init__.py:43` (`__all__` entry)

**Step 1: Remove the import of `_build_data_entry_filter_clauses` from line 9**

Delete line 9 entirely:
```python
from .data_filters import _build_data_entry_filter_clauses
```

**Step 2: Remove `_build_data_entry_filter_clauses` from `__all__` (line 43)**

Delete line 43:
```python
    "_build_data_entry_filter_clauses",
```

**Step 3: Verify file integrity**

Run: `python -c "import ast; ast.parse(open('models/__init__.py').read()); print('Syntax OK')"`
Expected: `Syntax OK`

---

### Task 3: Remove `apply_period_range_filter` from `services/period_filters.py`

**Files:**
- Modify: `services/period_filters.py:61-111` (function definition)

**Step 1: Delete the `apply_period_range_filter` function (lines 61-111)**

Remove the entire function definition and its body. Keep `parse_period_filter_value` (lines 9-38) and `period_index` (lines 41-58).

**Step 2: Verify file integrity**

Run: `python -c "import ast; ast.parse(open('services/period_filters.py').read()); print('Syntax OK')"`
Expected: `Syntax OK`

---

### Task 4: Verify no remaining references

**Step 1: Search for any remaining references to removed functions**

Run: `grep -r "_build_data_entry_filter_clauses\|apply_period_range_filter" --include="*.py" .`
Expected: No output (no references in Python files)

**Step 2: Verify imports still work**

Run: `python -c "from models import *; from services.period_filters import parse_period_filter_value, period_index; print('Imports OK')"`
Expected: `Imports OK`
