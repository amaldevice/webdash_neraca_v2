# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io

import pandas as pd
from flask import Response


# Canonical column order shared by CSV and Excel raw export (parity).
RAW_EXPORT_COLUMNS = [
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


def build_raw_data_export_response(entries: list, fmt: str) -> Response:
    """CSV or Excel attachment for filtered raw rows."""
    fmt = fmt.lower()
    if fmt == "excel":
        df = pd.DataFrame(entries, columns=RAW_EXPORT_COLUMNS) if entries else pd.DataFrame(
            columns=RAW_EXPORT_COLUMNS
        )
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
    writer.writerow(RAW_EXPORT_COLUMNS)
    for row in entries:
        writer.writerow([row.get(col, "") for col in RAW_EXPORT_COLUMNS])

    response = Response(buffer.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=raw-data.csv"
    return response
