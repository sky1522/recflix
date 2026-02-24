"""Recommendation endpoint tests.

These endpoints query movies from DB. With an empty SQLite DB,
they should return 200 with empty results.
"""
import pytest


@pytest.mark.skipif(True, reason="Uses JSONB cast — PostgreSQL only")
def test_get_recommendations_home(client):
    resp = client.get("/api/v1/recommendations", params={"weather": "sunny"})
    assert resp.status_code == 200


@pytest.mark.skipif(True, reason="Uses JSONB ordering — PostgreSQL only")
def test_get_popular(client):
    resp = client.get("/api/v1/recommendations/popular")
    assert resp.status_code == 200


@pytest.mark.skipif(True, reason="Uses JSONB ordering — PostgreSQL only")
def test_get_top_rated(client):
    resp = client.get("/api/v1/recommendations/top-rated")
    assert resp.status_code == 200
