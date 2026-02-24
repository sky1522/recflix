"""Health check endpoint tests."""


def test_health_returns_200(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_health_contains_components(client):
    resp = client.get("/api/v1/health")
    data = resp.json()
    assert "database" in data
    assert "redis" in data
    assert "environment" in data
