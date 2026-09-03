from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx

from app.core.config import settings
from app.schemas.profile import InvestmentProfile

_EVIDENCE_LABEL = {
    "market": "시세와 수급",
    "news": "최근 뉴스",
    "financial": "재무·공시 지표",
    "risk": "위험 요인",
}
_HORIZON_LABEL = {"short": "단기", "medium": "중기", "long": "장기"}


class MCPClientError(Exception):
    pass


class MCPClientTimeout(MCPClientError):
    pass


class MCPClientUnavailable(MCPClientError):
    pass


def _mock_personalized_checkpoints(profile: InvestmentProfile, one_line_summary: str) -> dict[str, Any]:
    """mcp_client가 아직 개인화를 만들지 못할 때 쓰는 표본 응답."""
    evidence_label = _EVIDENCE_LABEL.get(profile.preferred_evidence, profile.preferred_evidence)
    horizon_label = _HORIZON_LABEL.get(profile.investment_horizon, profile.investment_horizon)
    return {
        "personal_summary": f"{horizon_label} 관점에서 보면: {one_line_summary}",
        "priority_checks": [
            f"선호 근거인 {evidence_label}부터 확인해보자.",
            f"{profile.risk_profile} 성향에 맞는 변동성 수준인지 점검해보자.",
        ],
        "caution": "이 확인 포인트는 매수·매도를 추천하지 않으며 참고용 설명이다(Mock).",
    }


def _mock_common_analysis(
    company_name: str, stock_code: str, request_id: str, investment_profile: InvestmentProfile | None
) -> dict[str, Any]:
    """mcp_client 통합 서버가 아직 없을 때 Backend 단독 실행을 확인하기 위한 표본 응답."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    one_line_summary = f"{company_name}의 최근 흐름을 뉴스·공시·커뮤니티 반응과 함께 정리했다(Mock)."
    result: dict[str, Any] = {
        "request_id": request_id,
        "run_id": str(uuid4()),
        "status": "success",
        "termination_reason": "completed",
        "company": {"company_name": company_name, "stock_code": stock_code},
        "price": {
            "current_price": 70000,
            "change": 500,
            "change_rate": 0.72,
            "as_of": now,
        },
        "common_analysis": {
            "one_line_summary": one_line_summary,
            "market_temperature": {"score": 60, "label": "보통", "data_coverage": ["price"]},
            "evidence_level": {"level": "low", "reason": "mcp_client 연결 전 Mock 데이터다."},
            "news_summary": "mcp_client 연결 전 표본 뉴스 요약이다.",
            "disclosure_summary": "mcp_client 연결 전 표본 공시 요약이다.",
            "community_summary": "mcp_client 연결 전 표본 커뮤니티 요약이다.",
        },
        "sources": [],
        "partial_failures": [],
        "collected_at": now,
        "mock": True,
    }
    if investment_profile is not None:
        result["personalized_checkpoints"] = _mock_personalized_checkpoints(investment_profile, one_line_summary)
    return result


def fetch_common_analysis(
    company_name: str, stock_code: str, investment_profile: InvestmentProfile | None
) -> dict[str, Any]:
    request_id = str(uuid4())
    payload = {
        "request_id": request_id,
        "company": {"company_name": company_name, "stock_code": stock_code},
        "investment_profile": investment_profile.model_dump() if investment_profile else None,
        "requested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    try:
        response = httpx.post(
            f"{settings.mcp_client_url}/internal/v1/common-analyses",
            json=payload,
            timeout=settings.mcp_client_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        raise MCPClientTimeout() from None
    except httpx.HTTPError:
        return _mock_common_analysis(company_name, stock_code, request_id, investment_profile)
