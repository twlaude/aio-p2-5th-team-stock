from typing import Any
from uuid import uuid4

from app.clients.fgi_api import (
    CommunityFGIClient,
    FGIAPITimeout,
    FGIAPIUnauthorized,
    FGIAPIUnavailable,
)
from app.core.config import CommunityConfig, get_config
from app.schemas.reaction import ReactionRequest, ReactionResponse
from app.services.mock import build_mock_reaction

SERVICE_NAME = "community_mcp"


def error_response(status: str, code: str, message: str, retryable: bool) -> ReactionResponse:
    return {
        "request_id": str(uuid4()),
        "status": status,
        "error": {"service": SERVICE_NAME, "code": code, "message": message, "retryable": retryable},
    }


def map_upstream_response(payload: dict[str, Any], request: ReactionRequest) -> ReactionResponse:
    response: ReactionResponse = {
        "status": payload.get("status", "internal_error"),
        "company_name": request["company_name"],
        "stock_code": payload.get("stock_code") or request["stock_code"],
        "source_name": "태웅님 커뮤니티 서버",
    }
    if payload.get("source_name") is not None:
        response["source_detail"] = payload["source_name"]

    for key in ("sample_status", "period", "sample_size", "sentiment", "top_topics", "representative_evidence", "collected_at", "fgi_mean", "note", "supported_codes"):
        if key in payload:
            response[key] = payload[key]
    return response


def fetch_community_reaction(
    request: ReactionRequest,
    config: CommunityConfig | None = None,
    client: CommunityFGIClient | None = None,
) -> ReactionResponse:
    active_config = config or get_config()
    if active_config.mock_enabled:
        return build_mock_reaction(request["company_name"], request["stock_code"])

    owns_client = client is None
    active_client = client or CommunityFGIClient(
        active_config.api_url,
        active_config.api_token,
        active_config.timeout_sec,
    )
    try:
        payload = active_client.get_reaction(request["stock_code"], request["lookback_days"], request["limit"])
        return map_upstream_response(payload, request)
    except FGIAPITimeout:
        return error_response("timeout", "COMMUNITY_API_TIMEOUT", "커뮤니티 반응 조회가 시간 초과되었습니다.", True)
    except FGIAPIUnauthorized:
        return error_response("unauthorized", "COMMUNITY_API_UNAUTHORIZED", "커뮤니티 반응 조회 인증에 실패했습니다.", False)
    except FGIAPIUnavailable:
        return error_response("external_api_error", "COMMUNITY_API_UNAVAILABLE", "커뮤니티 반응을 일시적으로 가져오지 못했습니다.", True)
    finally:
        if owns_client:
            active_client.close()
