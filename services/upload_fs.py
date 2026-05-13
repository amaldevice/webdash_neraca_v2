# -*- coding: utf-8 -*-
"""Safe removal of upload working files (path guard + Windows-friendly retries)."""
from __future__ import annotations

import os
import time


def safe_remove_upload_working_file(
    file_path: str | None,
    *,
    upload_root: str | None = None,
    max_attempts: int = 3,
    delay_s: float = 0.2,
) -> None:
    """
    Remove ``file_path`` if it exists.

    When ``upload_root`` is set, only deletes if ``file_path`` resolves under that directory
    (prevents deleting arbitrary paths). ``PermissionError`` (e.g. WinError 32) is retried.
    """
    if not file_path or not os.path.isfile(file_path):
        return
    if upload_root:
        try:
            root = os.path.realpath(upload_root)
            fp = os.path.realpath(file_path)
            if fp != root and not fp.startswith(root + os.sep):
                return
        except OSError:
            return
    for attempt in range(max_attempts):
        try:
            os.remove(file_path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            if attempt >= max_attempts - 1:
                raise
            time.sleep(delay_s)
