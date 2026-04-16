# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io

import pandas as pd
from flask import Response


def build_raw_data_export_response(entries: list, fmt: str) -> Response:
    """CSV or Excel attachment for filtered raw rows."""
    fmt = fmt.lower()
    if fmt == "excel":
        columns = [
            "id",
            "uploader_name",
            "version",
            "dataset_code",
            "indicator_name",
            "value",
            "data_type",
            "time_period",
            "created_at",
            "year",
            "month",
            "quarter",
        ]
        df = pd.DataFrame(entries, columns=columns) if entries else pd.DataFrame(columns=columns)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return Response(
            output.getvalue(),
            headers={
                "Content-Disposition": "attachment; filename=raw-data.xlsx",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    headers = [
        "id",
        "uploader_name",
        "version",
        "dataset_code",
        "indicator_name",
        "value",
        "data_type",
        "time_period",
        "created_at",
    ]
    writer.writerow(headers)
    for row in entries:
        writer.writerow(
            [
                row["id"],
                row["uploader_name"],
                row["version"],
                row.get("dataset_code", ""),
                row["indicator_name"],
                row["value"],
                row["data_type"],
                row["time_period"],
                row["created_at"],
            ]
        )

    response = Response(buffer.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=raw-data.csv"
    return response
