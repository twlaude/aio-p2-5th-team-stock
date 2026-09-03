def test_login_success(client):
    response = client.post("/api/v1/auth/login", json={"username": "demo001", "password": "Demo1234!"})
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["user"]["username"] == "demo001"
    assert body["profile_completed"] is True


def test_login_wrong_password(client):
    response = client.post("/api/v1/auth/login", json={"username": "demo001", "password": "wrong"})
    assert response.status_code == 401


def test_signup_creates_new_user(client):
    body = {
        "username": "new_user",
        "password": "SafePass1!",
        "display_name": "새 사용자",
        "profile": {
            "experience_level": "beginner",
            "risk_profile": "balanced",
            "investment_horizon": "long",
            "preferred_evidence": "news",
        },
    }
    response = client.post("/api/v1/auth/signup", json=body)

    assert response.status_code == 200
    assert response.json()["user"]["username"] == "new_user"


def test_profile_requires_auth(client):
    response = client.get("/api/v1/profile")
    assert response.status_code == 401
