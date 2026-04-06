# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd
import plotly.express as px

from models import query_data_entries


def generate_indicator_line_chart(
    indicator: str,
    time_range: str = "all",
    period_start: str | None = None,
    period_end: str | None = None,
) -> str:
    """Build Plotly line chart JSON for one indicator (optional period bounds)."""
    entries = query_data_entries(
        indicator=indicator,
        limit=1000,
        period_start=period_start,
        period_end=period_end,
    )

    if not entries:
        return "<div class='no-data'>Tidak ada data untuk membuat plot</div>"

    df = pd.DataFrame(entries)
    df_filtered = df[df["indicator_name"] == indicator].copy()

    if df_filtered.empty:
        return f"<div class='error'>Tidak ada data untuk indikator '{indicator}'</div>"

    if time_range != "all":
        if time_range and "tanggal_data" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["tanggal_data"].str.startswith(time_range)]

    if "tanggal_data" in df_filtered.columns:
        df_filtered = df_filtered.sort_values("tanggal_data")
    else:
        df_filtered = df_filtered.sort_index()

    fig = px.line(
        df_filtered,
        x="tanggal_data" if "tanggal_data" in df_filtered.columns else df_filtered.index,
        y="value",
        title=f'Tren {indicator} ({time_range.replace("all", "Semua Periode")})',
        labels={
            "tanggal_data": "Periode",
            "value": "Nilai",
            "x": "Periode",
        },
        markers=True,
    )

    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
    )

    fig.update_layout(
        template="plotly_white",
        font=dict(size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Periode Waktu",
        yaxis_title="Nilai",
        showlegend=False,
        height=480,
    )

    return fig.to_json()
