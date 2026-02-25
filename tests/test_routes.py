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
    assert client.get("/aggregated").status_code == 200
    assert client.get("/preview-data").status_code == 200


def test_post_manual_minimal(client):
    response = client.post(
        "/manual",
        data={
            "uploader": "Tester",
            "version": "v1",
            "data_type": "flow",
            "time_period": "monthly",
            "indicator": "Inflasi",
            "value": "42.0",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    entries = query_data_entries(limit=10)
    assert len(entries) == 1


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
