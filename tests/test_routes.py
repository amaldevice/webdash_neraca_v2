from models import insert_entries, query_data_entries


def _seed_entry():
    return {
        "uploader_name": "Tester",
        "version": "v1",
        "template_type": "manual",
        "data_type": "flow",
        "time_period": "monthly",
        "indicator_name": "Inflasi",
        "value": 10.5,
        "unit": None,
        "region_code": None,
        "year": 2024,
        "month": 1,
        "quarter": None,
        "created_at": "2024-01-01T00:00:00",
    }


def test_get_routes(client):
    assert client.get("/").status_code == 200
    assert client.get("/preview-data").status_code == 200


def test_post_manual_minimal(client):
    response = client.post(
        "/manual",
        data={
            "uploader": "Tester",
            "version": "v1",
            "data_type": "flow",
            "time_period": "monthly",
            "period_date": "2024-01",
            "indicator": "Inflasi",
            "value": "42.0",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    # Check if data was actually saved
    entries = query_data_entries(limit=10)
    assert len(entries) == 1
    assert entries[0]["indicator_name"] == "Inflasi"
    assert entries[0]["value"] == 42.0
    assert entries[0]["year"] == 2024
    assert entries[0]["month"] == 1

    # Test quarterly input
    response_q = client.post(
        "/manual",
        data={
            "uploader": "Tester",
            "version": "v1",
            "data_type": "flow",
            "time_period": "quarterly",
            "period_date": "2024-Q2",
            "indicator": "GDP",
            "value": "1500.0",
        },
        follow_redirects=True,
    )
    assert response_q.status_code == 200
    entries = query_data_entries(limit=10)
    assert len(entries) == 2

    # Test yearly input
    response_y = client.post(
        "/manual",
        data={
            "uploader": "Tester",
            "version": "v1",
            "data_type": "stock",
            "time_period": "yearly",
            "period_date": "2024",
            "indicator": "Population",
            "value": "270000000",
        },
        follow_redirects=True,
    )
    assert response_y.status_code == 200
    entries = query_data_entries(limit=10)
    assert len(entries) == 3


def test_generate_plot_missing_indicator(client):
    response = client.post("/generate-plot", data={})
    payload = response.get_json()
    assert payload["error"] == "Pilih indikator terlebih dahulu"


def test_generate_plot_success(client):
    insert_entries([_seed_entry()])
    response = client.post(
        "/generate-plot",
        data={"indicator_filter": "Inflasi", "time_range": "all"},
    )
    payload = response.get_json()
    assert "plot_json" in payload
