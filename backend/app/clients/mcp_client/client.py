from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx

from app.core.config import settings


class MCPClientError(Exception):
    pass


class MCPClientTimeout(MCPClientError):
    pass


class MCPClientUnavailable(MCPClientError):
    pass


def _mock_common_analysis(company_name: str, stock_code: str, request_id: str) -> dict[str, Any]:
    """mcp_client 통합 서버가 아직 없을 때 Backend 단독 실행을 확인하기 위한 표본 응답."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
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
            "one_line_summary": f"{company_name}의 최근 흐름을 뉴스·공시·커뮤니티 반응과 함께 정리했다(Mock).",
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


def fetch_common_analysis(company_name: str, stock_code: str, question: str | None) -> dict[str, Any]:
    request_id = str(uuid4())
    payload = {
        "request_id": request_id,
        "company": {"company_name": company_name, "stock_code": stock_code},
        "question": question,
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
        return _mock_common_analysis(company_name, stock_code, request_id)
