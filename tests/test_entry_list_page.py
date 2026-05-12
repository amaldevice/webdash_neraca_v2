# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import Flask, request

from services.entry_list import (
    EXPORT_ENTRY_HARD_CAP,
    parse_entry_list_params_from_request,
)


def test_parse_entry_list_params_preview_vs_export_same_args():
    app = Flask(__name__)
    with app.test_request_context("/preview?data_type=flow&indicator=GDP&dataset_code=pinjaman"):
        p1 = parse_entry_list_params_from_request(request, filter_source="args")
        p2 = parse_entry_list_params_from_request(request, filter_source="args")
    assert p1 == p2
    assert p1.data_type == "flow"
    assert p1.indicator == "GDP"
    assert p1.dataset_code == "pinjaman"


def test_export_cap_constant_is_stable():
    assert EXPORT_ENTRY_HARD_CAP == 1000
