"""Basic tests proving that the Flask application starts successfully."""


def test_application_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "service": "MediQueue",
        "status": "ok",
    }


def test_api_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "ok": True,
        "service": "MediQueue API",
    }
