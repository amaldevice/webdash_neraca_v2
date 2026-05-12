# -*- coding: utf-8 -*-
"""Single seam: dataset slug → catalog + persistence code for upload/manual intake."""
from __future__ import annotations

from dataclasses import dataclass

from services.dataset_catalog import DatasetDefinition, get_dataset_or_none, normalize_dataset_code


@dataclass(frozen=True, slots=True)
class DatasetIntakeResolution:
    """Result of resolving a user-selected dataset slug for intake flows."""

    slug: str
    dataset_code: str
    definition: DatasetDefinition | None

    @property
    def is_known(self) -> bool:
        return self.definition is not None


def resolve_dataset_for_intake(slug: str | None) -> DatasetIntakeResolution:
    """
    Normalize slug and attach catalog row when present.

    Empty slug is treated as legacy/generic intake (no catalog row).
    """
    s = (slug or "").strip()
    if not s:
        return DatasetIntakeResolution(slug="", dataset_code="", definition=None)
    d = get_dataset_or_none(s)
    return DatasetIntakeResolution(slug=s, dataset_code=normalize_dataset_code(s), definition=d)
