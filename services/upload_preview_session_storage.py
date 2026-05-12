# -*- coding: utf-8 -*-
"""Domain seam for upload preview session persistence (file-backed adapter)."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from services import upload_preview as _preview_impl


@runtime_checkable
class UploadPreviewSessionStore(Protocol):
    """Load/save/delete preview payload keyed by opaque session token."""

    def load_session(self, session_token: str) -> dict | None: ...

    def save_session(self, session_token: str, payload: dict) -> None: ...

    def delete_session(self, session_token: str) -> None: ...


class FileBackedUploadPreviewSessionStore:
    """Adapter: sessions under configured upload storage root (implementation detail hidden from routes)."""

    def __init__(self, upload_storage_root: str) -> None:
        self._root = upload_storage_root

    def load_session(self, session_token: str) -> dict | None:
        return _preview_impl.load_preview_session(self._root, session_token)

    def save_session(self, session_token: str, payload: dict) -> None:
        _preview_impl.save_preview_session(self._root, session_token, payload)

    def delete_session(self, session_token: str) -> None:
        _preview_impl.delete_preview_session(self._root, session_token)


def file_backed_upload_preview_session_store(upload_storage_root: str) -> UploadPreviewSessionStore:
    return FileBackedUploadPreviewSessionStore(upload_storage_root)
