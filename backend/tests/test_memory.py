def test_get_memory_includes_long_term_profile(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}

    response = client.get("/api/v1/memories/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["long_term"] is not None
    assert body["long_term"]["risk_profile"] == "conservative"


def test_member_analysis_updates_short_term_memory(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}

    client.post("/api/v1/analyses", json={"query": "삼성전자"}, headers=headers)
    response = client.get("/api/v1/memories/me", headers=headers)

    assert response.status_code == 200
    short_term = response.json()["short_term"]
    assert short_term["recent_company_name"] == "삼성전자"
    assert short_term["recent_stock_code"] == "005930"
    assert "searched_at" in short_term
