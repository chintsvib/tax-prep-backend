def test_signup(client):
    resp = client.post("/auth/signup", json={
        "email": "new@example.com",
        "password": "secret123",
        "full_name": "New User",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert "access_token" in data
    assert data["user_id"] > 0


def test_signup_duplicate_email(client):
    client.post("/auth/signup", json={"email": "dup@example.com", "password": "pass"})
    resp = client.post("/auth/signup", json={"email": "dup@example.com", "password": "pass"})
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_login(client):
    client.post("/auth/signup", json={"email": "login@example.com", "password": "mypass"})
    resp = client.post("/auth/login", json={"email": "login@example.com", "password": "mypass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/auth/signup", json={"email": "wrong@example.com", "password": "correct"})
    resp = client.post("/auth/login", json={"email": "wrong@example.com", "password": "incorrect"})
    assert resp.status_code == 401


def test_me(client, auth_header):
    resp = client.get("/auth/me", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_me_no_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)
