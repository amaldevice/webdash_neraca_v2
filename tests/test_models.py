import models


def test_init_db_creates_file(db_path):
    assert db_path.exists()


def test_insert_single_entry_and_query(db_path):
    created = models.insert_single_entry(
        uploader="Tester",
        version="v1",
        data_type="flow",
        time_period="monthly",
        period_date="2024-01",
        indicator="Inflasi",
        value=12.5,
    )
    assert created is True
    rows = models.query_data_entries(limit=10)
    assert len(rows) == 1
    assert rows[0]["indicator_name"] == "Inflasi"
    assert rows[0]["year"] == 2024
    assert rows[0]["month"] == 1
    assert rows[0]["value"] == 12.5

    # Test quarterly insertion
    created_q = models.insert_single_entry(
        uploader="Tester",
        version="v1",
        data_type="flow",
        time_period="quarterly",
        period_date="2024-Q2",
        indicator="GDP",
        value=1500.0,
    )
    assert created_q is True
    rows = models.query_data_entries(limit=10)
    assert len(rows) == 2

    # Test yearly insertion
    created_y = models.insert_single_entry(
        uploader="Tester",
        version="v1",
        data_type="stock",
        time_period="yearly",
        period_date="2024",
        indicator="Population",
        value=270000000,
    )
    assert created_y is True
    rows = models.query_data_entries(limit=10)
    assert len(rows) == 3


def test_query_data_entries_with_value_min_filter(db_path):
    models.clear_all_data()
    models.insert_entries(
        [
            {"uploader_name": "A", "version": "v1", "template_type": "manual", "data_type": "flow", "time_period": "monthly",
             "indicator_name": "GDP", "value": 10.0, "year": 2024, "month": 1, "quarter": None},
            {"uploader_name": "B", "version": "v1", "template_type": "manual", "data_type": "flow", "time_period": "monthly",
             "indicator_name": "GDP", "value": 100.0, "year": 2024, "month": 2, "quarter": None},
        ]
    )
    rows = models.query_data_entries(limit=10, value_min=50.0)
    assert len(rows) == 1
    assert rows[0]["value"] == 100.0


def test_query_data_entries_with_value_range_filters(db_path):
    models.clear_all_data()
    models.insert_entries(
        [
            {"uploader_name": "A", "version": "v1", "template_type": "manual", "data_type": "flow", "time_period": "monthly",
             "indicator_name": "GDP", "value": 50.0, "year": 2024, "month": 1, "quarter": None},
            {"uploader_name": "B", "version": "v1", "template_type": "manual", "data_type": "flow", "time_period": "monthly",
             "indicator_name": "GDP", "value": 150.0, "year": 2024, "month": 2, "quarter": None},
            {"uploader_name": "C", "version": "v1", "template_type": "manual", "data_type": "flow", "time_period": "monthly",
             "indicator_name": "GDP", "value": 250.0, "year": 2024, "month": 3, "quarter": None},
        ]
    )
    rows = models.query_data_entries(limit=10, value_min=75.0, value_max=200.0)
    assert len(rows) == 1
    assert rows[0]["value"] == 150.0


def test_repositories_package_does_not_reexport_entry_list():
    """models.repositories __init__ should not re-export entry list helpers.
    Callers must import directly from models.repositories.entry_list."""
    import importlib
    pkg = importlib.import_module("models.repositories")
    assert not hasattr(pkg, "fetch_entries_for_list"), \
        "fetch_entries_for_list should not be importable from models.repositories directly"
    assert not hasattr(pkg, "count_entries_for_list"), \
        "count_entries_for_list should not be importable from models.repositories directly"
