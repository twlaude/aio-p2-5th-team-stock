def test_list_companies(client):
    response = client.get("/api/v1/companies")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["companies"][0]["company_name"] == "삼성전자"


def test_guest_analysis_hides_detail(client):
    response = client.post("/api/v1/analyses", json={"query": "삼성전자"})
    body = response.json()

    assert response.status_code == 200
    assert body["access_level"] == "guest"
    assert body["requires_login"] is True
    assert body["detail"] is None
    assert body["personalized_checkpoints"] is None


def test_member_analysis_includes_personalization(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}
    response = client.post("/api/v1/analyses", json={"query": "삼성전자"}, headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["access_level"] == "member"
    assert body["requires_login"] is False
    assert body["detail"] is not None
    assert body["personalized_checkpoints"]["priority_checks"]


def test_unsupported_company(client):
    response = client.post("/api/v1/analyses", json={"query": "존재하지않는회사"})
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "unsupported_company"
    assert "actions" in body
