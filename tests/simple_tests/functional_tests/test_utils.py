"""
Utilities untuk functional tests BPS Data Management System

Helper functions untuk:
- Membuat sample Excel files untuk testing
- Validasi response content
- Helper untuk assertions yang sering digunakan
- Setup/cleanup utilities
"""

import os
import tempfile
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any


def create_sample_excel_file(data: List[Dict[str, Any]], filename: str = None) -> str:
    """
    Membuat file Excel sample untuk testing upload

    Args:
        data: List dictionary berisi data untuk Excel
        filename: Nama file (optional, akan generate otomatis jika None)

    Returns:
        Path ke file Excel yang dibuat
    """
    if filename is None:
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        filename = temp_file.name
        temp_file.close()

    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)

    return filename


def get_sample_upload_data() -> List[Dict[str, Any]]:
    """
    Mendapatkan sample data untuk testing upload Excel

    Returns:
        List dictionary dengan struktur data yang valid
    """
    return [
        {
            'uploader_name': 'TestUser1',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'indicator_name': 'GDP',
            'value': 100.5,
            'year': 2024,
            'month': 1,
            'quarter': 1
        },
        {
            'uploader_name': 'TestUser1',
            'version': 'v1.0',
            'data_type': 'flow',
            'time_period': 'monthly',
            'indicator_name': 'Inflation',
            'value': 250.0,
            'year': 2024,
            'month': 2,
            'quarter': 1
        },
        {
            'uploader_name': 'TestUser2',
            'version': 'v1.1',
            'data_type': 'stock',
            'time_period': 'quarterly',
            'indicator_name': 'Population',
            'value': 150.75,
            'year': 2024,
            'month': None,
            'quarter': 2
        }
    ]


def get_sample_manual_entry_data() -> Dict[str, str]:
    """
    Mendapatkan sample data untuk testing manual entry

    Returns:
        Dictionary dengan form data untuk manual entry
    """
    return {
        'uploader': 'ManualUser',
        'version': 'v1.0',
        'data_type': 'flow',
        'time_period': 'monthly',
        'period_date': '2024-03',
        'indicator': 'ManualGDP',
        'value': '175.25'
    }


def assert_response_success(response, expected_status: int = 200) -> None:
    """
    Assert bahwa response berhasil dengan status code yang diharapkan

    Args:
        response: Flask response object
        expected_status: Expected status code (default 200)
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}"


def assert_response_redirect(response, expected_location_contains: str = None) -> None:
    """
    Assert bahwa response adalah redirect

    Args:
        response: Flask response object
        expected_location_contains: String yang harus ada di Location header
    """
    assert response.status_code == 302, \
        f"Expected redirect (302), got {response.status_code}"

    if expected_location_contains:
        location = response.headers.get('Location', '')
        assert expected_location_contains in location, \
            f"Expected '{expected_location_contains}' in redirect location, got '{location}'"


def assert_page_contains_text(response, text_list: List[str], case_sensitive: bool = False) -> None:
    """
    Assert bahwa response mengandung text tertentu

    Args:
        response: Flask response object
        text_list: List text yang harus ada di response
        case_sensitive: Apakah case sensitive (default False)
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.data, 'html.parser')
    page_text = soup.get_text()

    if not case_sensitive:
        page_text = page_text.lower()
        text_list = [text.lower() for text in text_list]

    for text in text_list:
        assert text in page_text, f"Expected text '{text}' not found in response"


def assert_page_contains_error(response, error_keywords: List[str] = None) -> None:
    """
    Assert bahwa response mengandung pesan error

    Args:
        response: Flask response object
        error_keywords: List keyword error yang diharapkan (default: ['error', 'gagal'])
    """
    if error_keywords is None:
        error_keywords = ['error', 'gagal', 'tidak valid']

    assert_page_contains_text(response, error_keywords, case_sensitive=False)


def assert_page_contains_success(response, success_keywords: List[str] = None) -> None:
    """
    Assert bahwa response mengandung pesan sukses

    Args:
        response: Flask response object
        success_keywords: List keyword sukses yang diharapkan (default: ['berhasil', 'success'])
    """
    if success_keywords is None:
        success_keywords = ['berhasil', 'success', 'sukses']

    assert_page_contains_text(response, success_keywords, case_sensitive=False)


def assert_form_has_fields(response, field_names: List[str]) -> None:
    """
    Assert bahwa form di response mengandung field yang diperlukan

    Args:
        response: Flask response object
        field_names: List nama field yang harus ada
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.data, 'html.parser')
    form = soup.find('form')

    assert form is not None, "Response harus mengandung form"

    for field_name in field_names:
        field = form.find('input', {'name': field_name}) or \
                form.find('select', {'name': field_name}) or \
                form.find('textarea', {'name': field_name})

        assert field is not None, f"Form harus memiliki field '{field_name}'"


def assert_csv_content_valid(csv_content: str, min_rows: int = 1) -> None:
    """
    Assert bahwa CSV content valid dan memiliki minimal baris tertentu

    Args:
        csv_content: String content dari CSV response
        min_rows: Minimal jumlah baris yang diharapkan (termasuk header)
    """
    import csv
    import io

    csv_reader = csv.reader(io.StringIO(csv_content))
    rows = list(csv_reader)

    assert len(rows) >= min_rows, f"CSV harus memiliki minimal {min_rows} baris, got {len(rows)}"

    # Validasi header ada
    if len(rows) > 0:
        header = rows[0]
        assert len(header) > 0, "CSV harus memiliki header"

        # Validasi semua baris memiliki jumlah kolom sama
        expected_cols = len(header)
        for i, row in enumerate(rows):
            assert len(row) == expected_cols, f"Baris {i} memiliki {len(row)} kolom, expected {expected_cols}"


def assert_excel_content_valid(excel_data: bytes, min_rows: int = 0) -> None:
    """
    Assert bahwa Excel content valid dan memiliki minimal baris tertentu

    Args:
        excel_data: Bytes dari Excel response
        min_rows: Minimal jumlah baris data (exclude header)
    """
    import io

    df = pd.read_excel(io.BytesIO(excel_data))

    assert len(df) >= min_rows, f"Excel harus memiliki minimal {min_rows} baris data, got {len(df)}"
    assert len(df.columns) > 0, "Excel harus memiliki kolom"


def cleanup_temp_file(file_path: str) -> None:
    """
    Cleanup temporary file dengan safe error handling

    Args:
        file_path: Path ke file yang akan dihapus
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        # Ignore cleanup errors
        pass


def create_test_excel_with_errors() -> str:
    """
    Membuat file Excel dengan data yang akan menyebabkan error

    Returns:
        Path ke file Excel yang dibuat
    """
    # Data dengan missing required fields
    error_data = [
        {
            'uploader_name': '',  # Empty uploader
            'version': 'v1.0',
            'indicator_name': 'GDP',
            'value': 100.5
            # Missing data_type, time_period, dll
        }
    ]

    return create_sample_excel_file(error_data)


def get_filter_test_cases() -> List[Dict[str, Any]]:
    """
    Mendapatkan test cases untuk berbagai kombinasi filter

    Returns:
        List dictionary dengan test cases filter
    """
    return [
        {'name': 'filter_uploader', 'params': {'uploader': 'Alice'}, 'expected_contains': ['Alice']},
        {'name': 'filter_data_type', 'params': {'data_type': 'flow'}, 'expected_contains': ['flow']},
        {'name': 'filter_time_period', 'params': {'time_period': 'monthly'}, 'expected_contains': ['monthly']},
        {'name': 'filter_indicator', 'params': {'indicator': 'GDP'}, 'expected_contains': ['GDP']},
        {'name': 'multiple_filters', 'params': {'uploader': 'Alice', 'data_type': 'flow'},
         'expected_contains': ['Alice', 'flow']},
    ]


def measure_response_time(func, *args, **kwargs) -> tuple:
    """
    Mengukur waktu response dari function call

    Args:
        func: Function yang akan diukur
        *args, **kwargs: Arguments untuk function

    Returns:
        Tuple (result, response_time_seconds)
    """
    import time

    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()

    return result, end_time - start_time