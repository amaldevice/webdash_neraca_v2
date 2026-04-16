# -*- coding: utf-8 -*-
"""Route GET /upload/template/<dataset_slug> (template per dataset)."""
from __future__ import annotations


def test_upload_template_ok(client):
    r = client.get("/upload/template/pinjaman")
    assert r.status_code == 200
    assert r.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment" in (r.headers.get("Content-Disposition") or "").lower()
    assert len(r.data) > 200


def test_upload_template_unknown_404(client):
    r = client.get("/upload/template/__no_such_slug__")
    assert r.status_code == 404
