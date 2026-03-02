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
