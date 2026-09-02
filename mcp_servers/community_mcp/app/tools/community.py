"""FastMCP tool implementation for community reaction."""
from typing import Any

from app.schemas.reaction import ReactionRequest
from app.services.reaction import error_response, fetch_community_reaction


def _invalid(message: str) -> dict[str, Any]:
    return error_response("invalid_request", "INVALID_REQUEST", message, False)


def get_community_reaction(
    company_name: str,
    stock_code: str,
    lookback_days: int = 7,
    limit: int = 100,
) -> dict[str, Any]:
    """Return recent community FGI reaction using the shared community contract.

    Input: company_name, six-digit stock_code, lookback_days 1..28, limit 1..500.
    Output: status, sample_status, period, sample_size, sentiment, topics,
    representative_evidence, source_name, collected_at, and contract error fields.
    """
    if not stock_code.isdigit() or len(stock_code) != 6:
        return _invalid("stock_code는 6자리 숫자여야 합니다.")
    if not 1 <= lookback_days <= 28:
        return _invalid("lookback_days는 1 이상 28 이하이어야 합니다.")
    if not 1 <= limit <= 500:
        return _invalid("limit는 1 이상 500 이하이어야 합니다.")

    request: ReactionRequest = {
        "company_name": company_name,
        "stock_code": stock_code,
        "lookback_days": lookback_days,
        "limit": limit,
    }
    return fetch_community_reaction(request)


def register_community_tools(mcp: Any) -> None:
    mcp.tool()(get_community_reaction)
