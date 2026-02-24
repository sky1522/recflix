"""Authentication endpoint tests."""


SIGNUP_URL = "/api/v1/auth/signup"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"

USER = {
    "email": "test@example.com",
    "password": "TestPassword123!",
    "nickname": "tester",
}


def _signup(client):
    return client.post(SIGNUP_URL, json=USER)


def test_signup_success(client):
    resp = _signup(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == USER["email"]


def test_signup_duplicate_email(client):
    _signup(client)
    resp = _signup(client)
    assert resp.status_code == 400


def test_login_success(client):
    _signup(client)
    resp = client.post(LOGIN_URL, json={"email": USER["email"], "password": USER["password"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    _signup(client)
    resp = client.post(LOGIN_URL, json={"email": USER["email"], "password": "wrong"})
    assert resp.status_code == 401


def test_refresh_token(client):
    _signup(client)
    login_resp = client.post(LOGIN_URL, json={"email": USER["email"], "password": USER["password"]})
    refresh = login_resp.json()["refresh_token"]
    resp = client.post(REFRESH_URL, json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
