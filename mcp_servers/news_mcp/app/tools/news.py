"""FastMCP tool implementation for news search."""
from typing import Any

from app.core.config import get_config
from app.schemas.news import NewsRequest
from app.services.news import error_response, fetch_news


def _invalid(message: str) -> dict[str, Any]:
    return error_response("invalid_request", "INVALID_REQUEST", message, False)


def search_news(
    company_name: str,
    stock_code: str,
    lookback_days: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Return recent news articles using the shared news contract.

    Input: company_name, six-digit stock_code, lookback_days 1..30 (기본 NEWS_LOOKBACK_DAYS=7),
    limit 1..10 (기본 NEWS_RESULT_LIMIT=10).
    Output: status, company_name, stock_code, articles, result_count, collected_at,
    and contract error fields.
    """
    config = get_config()
    if lookback_days is None:
        lookback_days = config.lookback_days
    if limit is None:
        limit = config.result_limit
    if not stock_code.isdigit() or len(stock_code) != 6:
        return _invalid("stock_code는 6자리 숫자여야 합니다.")
    if not 1 <= lookback_days <= 30:
        return _invalid("lookback_days는 1 이상 30 이하이어야 합니다.")
    if not 1 <= limit <= 10:
        return _invalid("limit는 1 이상 10 이하이어야 합니다.")

    request: NewsRequest = {
        "company_name": company_name,
        "stock_code": stock_code,
        "lookback_days": lookback_days,
        "limit": limit,
    }
    return fetch_news(request)


def register_news_tools(mcp: Any) -> None:
    mcp.tool()(search_news)
