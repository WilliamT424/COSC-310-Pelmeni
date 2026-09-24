def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_reports_ok_status(client):
    response = client.get("/health")
    assert response.json().get("status") == "ok"
