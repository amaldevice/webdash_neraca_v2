# -*- coding: utf-8 -*-
from __future__ import annotations


def test_preview_data_accepts_dataset_code_filter(client):
    """Entry list browse route stays wired through ``services.entry_list`` facade."""
    rv = client.get("/preview-data?dataset_code=pinjaman&limit=10")
    assert rv.status_code == 200
