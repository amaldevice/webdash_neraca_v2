# -*- coding: utf-8 -*-
"""Upload flow response types and factory."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class UploadFlowResponse:
    """Route applies `flashes` then either renders upload template or redirects to upload_data."""

    kind: Literal["render", "redirect"]
    flashes: list[tuple[str, str]] = field(default_factory=list)
    preview: dict[str, Any] | None = None
    upload_preview_token: str | None = None
    form_values: dict[str, Any] | None = None
    pop_upload_session_token: bool = False


@dataclass
class ManualFlowResponse:
    kind: Literal["render", "redirect"]
    flashes: list[tuple[str, str]] = field(default_factory=list)
    form_values: dict[str, Any] | None = None
    manual_duplicate: dict[str, Any] | None = None


def build_upload_response(
    kind: Literal["render", "redirect"],
    flashes: list[tuple[str, str]],
    *,
    preview: dict[str, Any] | None = None,
    upload_preview_token: str | None = None,
    form_values: dict[str, Any] | None = None,
    pop_upload_session_token: bool = False,
) -> UploadFlowResponse:
    """Buat response upload terstruktur agar konsisten di seluruh branch alur."""
    return UploadFlowResponse(
        kind=kind,
        flashes=flashes,
        preview=preview,
        upload_preview_token=upload_preview_token,
        form_values=form_values,
        pop_upload_session_token=pop_upload_session_token,
    )
