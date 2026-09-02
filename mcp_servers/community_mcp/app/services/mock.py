from app.schemas.reaction import FGIResponse, ReactionResponse


def build_mock_reaction(company_name: str, stock_code: str) -> ReactionResponse:
    return {
        "status": "success",
        "sample_status": "sufficient",
        "company_name": company_name,
        "stock_code": stock_code,
        "period": {"from": "2026-08-26T00:00:00Z", "to": "2026-09-01T09:00:00Z"},
        "sample_size": 100,
        "sentiment": {"positive_count": 35, "neutral_count": 40, "negative_count": 25},
        "top_topics": {
            "expectations": ["반도체 업황 회복과 저점 매수를 기대한다."],
            "concerns": ["단기 수급 변동성과 실적 확인 필요성을 우려한다."],
        },
        "representative_evidence": [
            {
                "text": "실적 회복 기대와 수급 부담이 함께 언급된다.",
                "sentiment": "neutral",
                "posted_at": "2026-09-01T01:00:00Z",
            }
        ],
        "source_name": "태웅님 커뮤니티 서버",
        "source_detail": "mock",
        "collected_at": "2026-09-01T09:00:00Z",
        "fgi_mean": 52.5,
        "fgi_latest": {
            "fgi": 52.5,
            "label": "중립",
            "as_of": "2026-09-01T09:00:00Z",
            "post_count": 100,
            "valence_percentile": 0.51,
        },
        "note": "Mock 응답이며 원문은 포함하지 않는다.",
        "mock": True,
    }


def build_mock_fgi(company_name: str, stock_code: str) -> FGIResponse:
    return {
        "request_id": "mock-fgi",
        "status": "success",
        "company_name": company_name,
        "stock_code": stock_code,
        "fgi": 52.5,
        "label": "중립",
        "as_of": "2026-09-01T09:00:00Z",
        "post_count": 100,
        "summary": "Mock 공포탐욕 지수 응답이다.",
        "warnings": [],
        "source_name": "태웅님 커뮤니티 서버",
        "source_detail": "mock",
        "collected_at": "2026-09-01T09:00:00Z",
        "mock": True,
    }
