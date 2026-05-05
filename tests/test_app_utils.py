from services.list_view import EntryListParams


def test_entry_list_params_query_kwargs():
    p = EntryListParams.from_request_strings(
        data_type="flow",
        time_period="monthly",
        uploader="u1",
        indicator="GDP",
        period_start="2024-01",
        period_end="2024-03",
        value_min=1.0,
        value_max=9.0,
    )
    qkw = p.to_query_kwargs()
    assert qkw["data_type"] == "flow"
    assert qkw["time_period"] == "monthly"
    assert qkw["uploader"] == "u1"
    assert qkw["indicator"] == "GDP"


def test_allowed_file(app_module):
    assert app_module.allowed_file("data.xlsx") is True
    assert app_module.allowed_file("data.xls") is True
    assert app_module.allowed_file("data.csv") is False
    assert app_module.allowed_file("data") is False


def test_validate_metadata(app_module):
    assert app_module.validate_metadata("flow", "monthly") == []
    errors = app_module.validate_metadata("invalid", "bad")
    assert "Tipe data tidak valid." in errors
    assert "Periode tidak valid." in errors


def test_build_manual_entry(app_module):
    entry = app_module._build_manual_entry(
        "Uploader",
        "v1",
        "flow",
        "monthly",
        "2024-01",
        "Inflasi",
        "123.45",
    )
    assert entry is not None
    assert entry["data_type"] == "flow"
    assert entry["time_period"] == "monthly"
    assert entry["value"] == 123.45
    assert entry["year"] == 2024
    assert entry["month"] == 1

    # Test invalid value
    assert app_module._build_manual_entry(
        "Uploader",
        "v1",
        "flow",
        "monthly",
        "2024-01",
        "Inflasi",
        "not-a-number",
    ) is None

    # Test quarterly format
    entry_quarterly = app_module._build_manual_entry(
        "Uploader",
        "v1",
        "flow",
        "quarterly",
        "2024-Q1",
        "GDP",
        "500.0",
    )
    assert entry_quarterly is not None
    assert entry_quarterly["quarter"] == 1
    # Test quarterly fallback with monthly marker
    entry_quarterly_marker = app_module._build_manual_entry(
        "Uploader",
        "v1",
        "flow",
        "quarterly",
        "2024-01",
        "GDP",
        "500.0",
    )
    assert entry_quarterly_marker is not None
    assert entry_quarterly_marker["year"] == 2024
    assert entry_quarterly_marker["month"] == 1
    assert entry_quarterly_marker["quarter"] == 1

    # Test yearly format
    entry_yearly = app_module._build_manual_entry(
        "Uploader",
        "v1",
        "stock",
        "yearly",
        "2024",
        "Population",
        "270000000",
    )
    assert entry_yearly is not None
    assert entry_yearly["year"] == 2024
    assert entry_yearly["month"] is None
    assert entry_yearly["quarter"] is None

    # Test yearly fallback with monthly marker format
    entry_yearly_marker = app_module._build_manual_entry(
        "Uploader",
        "v1",
        "stock",
        "yearly",
        "2024-01",
        "Population",
        "270000001",
    )
    assert entry_yearly_marker is not None
    assert entry_yearly_marker["year"] == 2024
    assert entry_yearly_marker["month"] == 1
    assert entry_yearly_marker["quarter"] is None
