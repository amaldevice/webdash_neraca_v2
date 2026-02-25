import models


def test_init_db_creates_file(db_path):
    assert db_path.exists()


def test_insert_single_entry_and_query(db_path):
    created = models.insert_single_entry(
        uploader="Tester",
        version="v1",
        data_type="flow",
        time_period="monthly",
        indicator="Inflasi",
        value=12.5,
    )
    assert created is True
    rows = models.query_data_entries(limit=10)
    assert len(rows) == 1
    assert rows[0]["indicator_name"] == "Inflasi"
