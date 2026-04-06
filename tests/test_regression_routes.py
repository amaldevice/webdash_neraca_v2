# -*- coding: utf-8 -*-
"""Smoke regression: main GET routes respond after factory + route registration refactor."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/upload",
        "/manual",
        "/preview-data",
        "/aggregated",
    ],
)
def test_main_get_routes_ok(client, path):
    rv = client.get(path)
    assert rv.status_code == 200


def test_export_get_csv_empty_ok(client):
    rv = client.get("/export?format=csv")
    assert rv.status_code == 200
