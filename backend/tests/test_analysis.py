import pytest

from app.services.analysis.narrative import josa, pick_topic


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


def test_guest_one_liner_uses_frontend_rule(client):
    response = client.post("/api/v1/analyses", json={"query": "삼성전자"})

    assert response.json()["one_line_summary"] == (
        "뉴스는 HBM 메모리에 쏠려 있고, 공식 확인은 아직 조금이에요. "
        "커뮤니티는 기대가 앞서요."
    )


def test_member_personal_summary_uses_risk_gap_rule(client, member_token):
    response = client.post(
        "/api/v1/analyses",
        json={"query": "삼성전자"},
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.json()["personalized_checkpoints"]["personal_summary"] == (
        "무리 없는 구간이에요. 삼성전자는 관심과 확인된 재료가 비슷해요. "
        "손실을 피하는 걸 우선하는 오래 들고 가는 편인 당신은 HBM 메모리 실적 흐름만 꾸준히 보면 돼요."
    )


@pytest.mark.parametrize(
    ("word", "expected"),
    [("삼성", "삼성은"), ("삼성전자", "삼성전자는"), ("HBM", "HBM는")],
)
def test_josa_matches_frontend_rule(word, expected):
    assert josa(word, "은", "는") == expected


def test_pick_topic_uses_fixed_fallback_without_community_topics():
    sources = [{"source_type": "news", "title": "제목에서 주제를 뽑으면 안 됨"}]

    assert pick_topic(sources, "최근 이슈") == "최근 이슈"
