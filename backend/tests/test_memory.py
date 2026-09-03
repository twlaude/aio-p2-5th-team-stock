def test_get_memory_includes_long_term_profile(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}

    response = client.get("/api/v1/memories/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["long_term"] is not None
    assert body["long_term"]["risk_profile"] == "conservative"
