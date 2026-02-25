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
        "Flow",
        "Monthly",
        "Inflasi",
        "123.45",
    )
    assert entry is not None
    assert entry["data_type"] == "flow"
    assert entry["time_period"] == "monthly"
    assert entry["value"] == 123.45

    assert app_module._build_manual_entry(
        "Uploader",
        "v1",
        "flow",
        "monthly",
        "Inflasi",
        "not-a-number",
    ) is None
