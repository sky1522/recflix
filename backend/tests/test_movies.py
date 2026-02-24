"""Movie endpoint tests.

Note: SQLite in-memory DB has no seed data, so list/search tests
verify response structure rather than data content.
PostgreSQL-specific features (pg_trgm, JSONB) are skipped.
"""
import pytest


def test_get_movies_returns_200(client):
    resp = client.get("/api/v1/movies")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


def test_get_movies_with_genre_filter(client):
    resp = client.get("/api/v1/movies", params={"genres": "Action"})
    assert resp.status_code == 200


def test_get_movie_not_found(client):
    resp = client.get("/api/v1/movies/999999")
    assert resp.status_code == 404


@pytest.mark.skipif(True, reason="autocomplete uses pg_trgm (PostgreSQL only)")
def test_autocomplete(client):
    resp = client.get("/api/v1/movies/search/autocomplete", params={"query": "test"})
    assert resp.status_code == 200
