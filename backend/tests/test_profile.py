def _signup(client, username):
    body = {
        "username": username,
        "password": "SafePass1!",
        "display_name": "테스트 사용자",
        "profile": {
            "experience_level": "beginner",
            "risk_profile": "conservative",
            "investment_horizon": "long",
            "preferred_evidence": "news",
        },
    }
    response = client.post("/api/v1/auth/signup", json=body)
    return response.json()["access_token"]


def test_get_and_update_profile(client):
    token = _signup(client, "profile_test_user")
    headers = {"Authorization": f"Bearer {token}"}

    get_response = client.get("/api/v1/profile", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["risk_profile"] == "conservative"

    update_body = {
        "experience_level": "experienced",
        "risk_profile": "aggressive",
        "investment_horizon": "short",
        "preferred_evidence": "market",
    }
    put_response = client.put("/api/v1/profile", json=update_body, headers=headers)
    assert put_response.status_code == 200
    assert put_response.json() == update_body
