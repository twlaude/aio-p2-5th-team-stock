import pytest

from app.core.config import settings
from app.schemas.analysis import EvidenceLevel, MarketTemperature
from app.schemas.profile import InvestmentProfile

from app.services.analysis.narrative import compose_one_liner, compose_personal, josa, pick_topic


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
    assert body["price"]["volume_basis"] == "last_session"
    assert body["price"]["volume_as_of"] == "2026-09-03"


def test_member_analysis_includes_personalization(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}
    response = client.post("/api/v1/analyses", json={"query": "삼성전자"}, headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["access_level"] == "member"
    assert body["requires_login"] is False
    assert body["detail"] is not None
    assert body["detail"]["market_temperature"]["weight_covered"] == 100
    assert body["personalized_checkpoints"]["priority_checks"]


@pytest.mark.parametrize(("payload", "expected"), [({}, 100), ({"weight_covered": 55}, 55)])
def test_market_temperature_weight_covered_default_and_passthrough(payload, expected):
    temperature = MarketTemperature(
        score=60,
        label="보통",
        data_coverage=["price", "news"],
        **payload,
    )

    assert temperature.weight_covered == expected


@pytest.mark.parametrize("weight_covered", [-1, 101])
def test_market_temperature_rejects_out_of_range_weight_covered(weight_covered):
    with pytest.raises(ValueError):
        MarketTemperature(
            score=60,
            label="보통",
            data_coverage=["price", "news"],
            weight_covered=weight_covered,
        )


def test_unsupported_company(client):
    response = client.post("/api/v1/analyses", json={"query": "존재하지않는회사"})
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "unsupported_company"
    assert "actions" in body


def test_guest_one_liner_uses_frontend_rule(client, monkeypatch):
    # Agent 서사가 없거나 실패한 경우 Backend가 프론트 규칙으로 조립한다.
    monkeypatch.setattr(settings, "narrative_source", "backend")
    response = client.post("/api/v1/analyses", json={"query": "삼성전자"})

    assert response.json()["one_line_summary"] == (
        "뉴스는 HBM 메모리에 쏠려 있고, 공식 확인은 아직 조금이에요. "
        "커뮤니티는 기대가 앞서요."
    )


def test_agent_narrative_wins_when_agent_succeeded(client, member_token):
    # 기본(agent_first): MCP Client Agent가 완성한 서사를 그대로 화면에 보낸다.
    response = client.post(
        "/api/v1/analyses",
        json={"query": "삼성전자"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    body = response.json()

    assert body["one_line_summary"].endswith("(Mock).")
    assert body["personalized_checkpoints"]["personal_summary"].startswith("장기 관점에서 보면")


def test_backend_composes_when_agent_failed(client, member_token, monkeypatch):
    from app.clients.mcp_client import client as mcp_client_module

    original = mcp_client_module.fetch_common_analysis

    def failed_agent(*args, **kwargs):
        raw = original(*args, **kwargs)
        raw["partial_failures"] = [{"service": "openai", "status": "model_error", "message": "x"}]
        return raw

    monkeypatch.setattr("app.services.analysis.service.mcp_client.fetch_common_analysis", failed_agent)
    response = client.post(
        "/api/v1/analyses",
        json={"query": "삼성전자"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    body = response.json()

    assert body["one_line_summary"].startswith("뉴스는 HBM 메모리에 쏠려 있고")
    assert body["personalized_checkpoints"]["personal_summary"].startswith("무리 없는 구간이에요.")


def test_member_personal_summary_uses_risk_gap_rule(client, member_token, monkeypatch):
    monkeypatch.setattr(settings, "narrative_source", "backend")
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


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        ("high", "관련 공시가 실제로 있어요"),
        ("medium", "주요 공시는 있지만 지금 화제와는 달라요"),
    ],
)
def test_one_liner_uses_issue_connection_evidence_copy(level, expected):
    assert expected in compose_one_liner("공급계약", level, 60, 1)


@pytest.mark.parametrize(
    ("preferred_evidence", "expected"),
    [
        ("financial", "최근 사업보고서의 매출·영업이익 흐름"),
        ("news", "최근 기사 내용이 공시로 확인되는지"),
        ("market", "거래량이 평소보다 늘었는지"),
        ("risk", "사업보고서의 위험 요인 중 지금 현실화된 게 있는지"),
    ],
)
def test_personalized_first_check_follows_preferred_evidence(preferred_evidence, expected):
    profile = InvestmentProfile(
        experience_level="beginner",
        risk_profile="conservative",
        investment_horizon="long",
        preferred_evidence=preferred_evidence,
    )

    result = compose_personal("삼성전자", "공급계약", 60, "high", profile)

    assert result.priority_checks[0] == expected


def test_evidence_level_accepts_and_preserves_issue_match_fields():
    evidence = EvidenceLevel(
        level="high",
        reason="공급계약 공시와 맞아요",
        matched=[
            {
                "issue": "대규모 공급계약 효과",
                "report_name": "단일판매ㆍ공급계약체결",
                "receipt_number": "202609040101",
                "published_at": "2026-09-04T00:00:00Z",
            }
        ],
        unmatched=["업황"],
        material_count=1,
    )

    assert evidence.model_dump()["matched"][0]["receipt_number"] == "202609040101"
