# -*- coding: utf-8 -*-
import csv
import io
import json
import os
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from flask import Flask, Response, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

from aggregator import fetch_aggregated_summary, refresh_aggregated_summary
from excel_parser import parse_excel
from models import (
    init_db, insert_entries, query_data_entries, get_total_entries_count,
    delete_data_entry, delete_data_by_filter, update_data_entry, insert_single_entry,
    get_filter_options, update_data_entry_full, get_unique_indicators
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {"xls", "xlsx"}
ALLOWED_DATA_TYPES = {"flow", "stock"}
ALLOWED_TIME_PERIODS = {"monthly", "quarterly", "yearly"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "change-me-for-production")

init_db()

def allowed_file(filename: str) -> bool:
    """Validate file extensions for Excel uploads."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_metadata(data_type: str, time_period: str) -> list[str]:
    errors = []
    if data_type.lower() not in ALLOWED_DATA_TYPES:
        errors.append("Tipe data tidak valid.")
    if time_period.lower() not in ALLOWED_TIME_PERIODS:
        errors.append("Periode tidak valid.")
    return errors


@app.route("/", methods=["GET"])
def landing_page():
    summary = fetch_aggregated_summary()
    return render_template("landing.html", summary=summary)


@app.route("/upload", methods=["GET", "POST"])
def upload_data():
    if request.method == "POST":
        uploader = request.form.get("uploader", "").strip()
        version = request.form.get("version", "").strip()
        data_type = request.form.get("data_type", "flow").strip()
        time_period = request.form.get("time_period", "monthly").strip()
        file = request.files.get("excel_file")
        errors = []

        if not uploader:
            errors.append("Nama pengupload wajib diisi.")
        if not version:
            errors.append("Versioning wajib diisi.")
        if not file or not allowed_file(file.filename):
            errors.append("Harus mengunggah file Excel (.xls/.xlsx).")
        errors.extend(validate_metadata(data_type, time_period))

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            filename = secure_filename(file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            destination = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(destination)
            entries = parse_excel(destination, uploader, version, data_type, time_period)
            if not entries:
                flash("File Excel tidak berisi data yang valid.", "error")
            else:
                try:
                    insert_entries(entries)
                    refresh_aggregated_summary()
                    flash(f"{len(entries)} baris data berhasil disimpan.", "success")
                except sqlite3.IntegrityError as e:
                    # Handle database constraint violations
                    error_msg = str(e)
                    if "UNIQUE constraint failed" in error_msg:
                        flash("Data dengan uploader, versi, dan indikator yang sama sudah ada. Gunakan versi yang berbeda atau periksa file Excel Anda.", "error")
                    else:
                        flash(f"Terjadi kesalahan database: {error_msg}", "error")
                except Exception as e:
                    # Handle other unexpected errors
                    flash(f"Terjadi kesalahan saat menyimpan data: {str(e)}", "error")
            return redirect(url_for("upload_data"))

    return render_template("upload.html", mode="upload")


@app.route("/manual", methods=["GET", "POST"])
def manual_input():
    if request.method == "POST":
        uploader = request.form.get("uploader", "").strip()
        version = request.form.get("version", "").strip()
        data_type = request.form.get("data_type", "flow").strip()
        time_period = request.form.get("time_period", "monthly").strip()
        indicator = request.form.get("indicator", "").strip()
        value = request.form.get("value", "").strip()

        if not uploader or not version or not indicator or not value:
            flash("Semua field metadata dan data harus diisi.", "error")
        else:
            validation_errors = validate_metadata(data_type, time_period)
            if validation_errors:
                for err in validation_errors:
                    flash(err, "error")
            else:
                manual_entry = _build_manual_entry(
                    uploader, version, data_type, time_period, indicator, value
                )
                if manual_entry is None:
                    flash("Nilai indikator tidak valid.", "error")
                else:
                    insert_entries([manual_entry])
                    refresh_aggregated_summary()
                    flash("Input manual dicatat dan disimpan.", "success")
                    return redirect(url_for("manual_input"))

    return render_template("upload.html", mode="manual")


def _build_manual_entry(
    uploader: str,
    version: str,
    data_type: str,
    time_period: str,
    indicator: str,
    value: str,
) -> dict | None:
    try:
        parsed_value = float(value)
    except ValueError:
        return None
    return {
        "uploader_name": uploader,
        "version": version,
        "template_type": "manual",
        "data_type": data_type.lower() or "flow",
        "time_period": time_period.lower() or "monthly",
        "indicator_name": indicator,
        "value": parsed_value,
        "unit": None,
        "region_code": None,
        "year": None,
        "month": None,
        "quarter": None,
        "created_at": datetime.utcnow().isoformat(),
    }


@app.route("/preview-data", methods=["GET"])
def preview_data():
    # Get filter parameters
    data_type = request.args.get("data_type", "")
    time_period = request.args.get("time_period", "")
    uploader = request.args.get("uploader", "")
    indicator = request.args.get("indicator", "")

    # Get pagination parameters
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))  # Default 20 rows

    # Validate limit options
    if limit not in [10, 20, 50]:
        limit = 20

    # Calculate offset for pagination
    offset = (page - 1) * limit

    summary = fetch_aggregated_summary()
    entries = query_data_entries(data_type=data_type or None, time_period=time_period or None,
                               limit=limit, offset=offset)

    # Apply additional filters if provided
    if uploader:
        entries = [e for e in entries if uploader.lower() in e["uploader_name"].lower()]
    if indicator:
        entries = [e for e in entries if indicator.lower() in e["indicator_name"].lower()]

    # Get total count for pagination (considering all filters)
    total_entries = get_total_entries_count(data_type=data_type or None, time_period=time_period or None)
    # Adjust total for additional filters (simplified approach)
    if uploader or indicator:
        total_entries = len(entries) + offset  # Approximate for pagination

    total_pages = (total_entries + limit - 1) // limit  # Ceiling division

    filters = {
        "data_type": data_type,
        "time_period": time_period,
        "uploader": uploader,
        "indicator": indicator,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_entries": total_entries
    }

    # Get filter options for autocomplete
    filter_options = get_filter_options()

    return render_template(
        "preview.html", summary=summary, entries=entries, filters=filters, filter_options=filter_options
    )


@app.route("/export", methods=["GET"])
def export_data():
    fmt = request.args.get("format", "csv").lower()
    data_type = request.args.get("data_type")
    time_period = request.args.get("time_period")
    entries = query_data_entries(data_type=data_type, time_period=time_period, limit=1000)
    if fmt == "excel":
        df = pd.DataFrame(entries)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        headers = {
            "Content-Disposition": "attachment; filename=raw-data.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return Response(output.getvalue(), headers=headers)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    headers = ["id", "uploader_name", "version", "indicator_name", "value", "data_type", "time_period", "created_at"]
    writer.writerow(headers)
    for row in entries:
        writer.writerow(
            [
                row["id"],
                row["uploader_name"],
                row["version"],
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


@app.route("/aggregated", methods=["GET"])
def aggregated_summary():
    summary = fetch_aggregated_summary()
    # Get unique indicators for filter dropdown
    indicators = get_unique_indicators()
    summary_with_indicators = dict(summary)
    summary_with_indicators['indicators'] = indicators
    return render_template("aggregated.html", summary=summary_with_indicators)


@app.route("/generate-plot", methods=["POST"])
def generate_plot():
    indicator = request.form.get("indicator_filter", "").strip()
    time_range = request.form.get("time_range", "all")

    if not indicator:
        return jsonify({"plot_html": "<div class='error'>Pilih indikator terlebih dahulu</div>"})

    # Generate line chart for selected indicator
    plot_html = generate_indicator_line_chart(indicator, time_range)

    return jsonify({"plot_html": plot_html})


def generate_indicator_line_chart(indicator, time_range="all"):
    """Generate line chart for a specific indicator with time filtering"""

    # Get data for specific indicator
    entries = query_data_entries(limit=1000)

    if not entries:
        return "<div class='no-data'>Tidak ada data untuk membuat plot</div>"

    # Convert to DataFrame
    df = pd.DataFrame(entries)

    # Filter by selected indicator
    df_filtered = df[df['indicator_name'] == indicator].copy()

    if df_filtered.empty:
        return f"<div class='error'>Tidak ada data untuk indikator '{indicator}'</div>"

    # Apply time range filter
    if time_range != "all":
        if 'tanggal_data' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['tanggal_data'].str.startswith(time_range)]

    # Sort by date for proper line chart
    if 'tanggal_data' in df_filtered.columns:
        df_filtered = df_filtered.sort_values('tanggal_data')
    else:
        df_filtered = df_filtered.sort_index()

    # Create line chart
    fig = px.line(
        df_filtered,
        x='tanggal_data' if 'tanggal_data' in df_filtered.columns else df_filtered.index,
        y='value',
        title=f'Tren {indicator} ({time_range.replace("all", "Semua Periode")})',
        labels={
            'tanggal_data': 'Periode',
            'value': 'Nilai',
            'x': 'Periode'
        },
        markers=True  # Add markers for better visibility
    )

    # Update line appearance
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )

    # Update layout
    fig.update_layout(
        template='plotly_white',
        font=dict(size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Periode Waktu",
        yaxis_title="Nilai",
        showlegend=False  # Hide legend since only one line
    )

    # Convert to HTML
    # NOTE: Using include_plotlyjs=True inlines the entire Plotly.js bundle into
    # every response (very large). This can make the /generate-plot response
    # feel like it "doesn't work" on slower machines/browsers.
    # Using CDN keeps responses small and usually fixes the UX.
    plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    return plot_html


@app.route("/data-management", methods=["GET", "POST"])
def data_management():
    # Handle filters
    data_type = request.args.get("data_type", "")
    time_period = request.args.get("time_period", "")
    uploader = request.args.get("uploader", "")
    indicator = request.args.get("indicator", "")

    # Handle CRUD operations
    if request.method == "POST":
        action = request.form.get("action")

        if action == "delete_single":
            entry_id = request.form.get("entry_id")
            if entry_id:
                delete_data_entry(entry_id)
                flash("Data berhasil dihapus.", "success")

        elif action == "delete_by_filter":
            deleted_count = delete_data_by_filter(
                data_type=data_type or None,
                time_period=time_period or None,
                uploader=uploader or None,
                indicator=indicator or None
            )
            flash(f"{deleted_count} data berhasil dihapus berdasarkan filter.", "success")

        elif action == "update":
            entry_id = request.form.get("entry_id")
            update_uploader = request.form.get("update_uploader", "").strip()
            update_version = request.form.get("update_version", "").strip()
            update_indicator = request.form.get("update_indicator", "").strip()
            update_value = request.form.get("update_value", "").strip()
            update_data_type = request.form.get("update_data_type", "").strip()
            update_time_period = request.form.get("update_time_period", "").strip()

            if entry_id and all([update_uploader, update_version, update_indicator, update_value]):
                try:
                    update_data_entry_full(entry_id, {
                        "uploader_name": update_uploader,
                        "version": update_version,
                        "indicator_name": update_indicator,
                        "value": float(update_value),
                        "data_type": update_data_type,
                        "time_period": update_time_period
                    })
                    flash("Data berhasil diperbarui.", "success")
                    # Clear cache after update
                    refresh_aggregated_summary()
                except ValueError:
                    flash("Nilai harus berupa angka.", "error")
                except Exception as e:
                    flash(f"Error updating data: {str(e)}", "error")

        elif action == "insert":
            insert_uploader = request.form.get("insert_uploader", "").strip()
            insert_version = request.form.get("insert_version", "").strip()
            insert_data_type = request.form.get("insert_data_type", "").strip()
            insert_time_period = request.form.get("insert_time_period", "").strip()
            insert_indicator = request.form.get("insert_indicator", "").strip()
            insert_value = request.form.get("insert_value", "").strip()

            if all([insert_uploader, insert_version, insert_indicator, insert_value]):
                try:
                    insert_single_entry(
                        uploader=insert_uploader,
                        version=insert_version,
                        data_type=insert_data_type,
                        time_period=insert_time_period,
                        indicator=insert_indicator,
                        value=float(insert_value)
                    )
                    flash("Data baru berhasil ditambahkan.", "success")
                    # Clear cache after insert
                    refresh_aggregated_summary()
                except ValueError:
                    flash("Nilai harus berupa angka.", "error")
            else:
                flash("Semua field harus diisi.", "error")

        return redirect(url_for("data_management", data_type=data_type, time_period=time_period,
                              uploader=uploader, indicator=indicator))

    # Get data for display
    entries = query_data_entries(data_type=data_type or None, time_period=time_period or None,
                               limit=50)  # Show more for management

    # Apply additional filters if provided
    if uploader:
        entries = [e for e in entries if uploader.lower() in e["uploader_name"].lower()]
    if indicator:
        entries = [e for e in entries if indicator.lower() in e["indicator_name"].lower()]

    filters = {
        "data_type": data_type,
        "time_period": time_period,
        "uploader": uploader,
        "indicator": indicator
    }

    return render_template("data_management.html", entries=entries, filters=filters)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("FLASK_RUN_PORT", 5000)))
