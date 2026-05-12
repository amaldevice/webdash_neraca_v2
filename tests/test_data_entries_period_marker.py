# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import request

from services.entry_list_page import parse_entry_list_params_from_request
from services.request_params import data_entries_period_marker_range_from_request


def test_period_marker_range_matches_args_vs_values(app_module):
    app = app_module.app
    with app.test_request_context(
        "/preview-data",
        query_string={
            "start_period": " 2024-01 ",
            "end_period": "2024-03",
            "data_type": "flow",
            "time_period": "monthly",
        },
    ):
        s1, e1 = data_entries_period_marker_range_from_request(request, filter_source="args")
        assert s1 == "2024-01"
        assert e1 == "2024-03"

    with app.test_request_context(
        "/data-management",
        method="POST",
        data={
            "start_period": "2023-Q1",
            "end_period": "2023-Q4",
            "data_type": "flow",
            "time_period": "quarterly",
        },
    ):
        s2, e2 = data_entries_period_marker_range_from_request(request, filter_source="values")
        assert s2 == "2023-Q1"
        assert e2 == "2023-Q4"


def test_parse_entry_list_uses_period_marker_facade(app_module):
    app = app_module.app
    with app.test_request_context(
        "/export",
        query_string={
            "start_period": "2022-06",
            "end_period": "2022-12",
            "data_type": "",
            "time_period": "",
            "uploader": "",
            "indicator": "",
            "dataset_code": "",
        },
    ):
        p = parse_entry_list_params_from_request(request, filter_source="args")
        assert p.period_start == "2022-06"
        assert p.period_end == "2022-12"
