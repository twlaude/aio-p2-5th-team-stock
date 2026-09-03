from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from typing import Any
from uuid import uuid4

from app.clients.naver_news import (
    NaverNewsAPITimeout,
    NaverNewsAPIUnauthorized,
    NaverNewsAPIUnavailable,
    NaverNewsClient,
)
from app.core.config import NewsConfig, get_config
from app.schemas.news import Article, ErrorDetail, NewsRequest, NewsResponse
from app.services.mock import build_mock_news

SERVICE_NAME = "news_mcp"
_TAG_RE = re.compile(r"<[^>]+>")


def error_response(status: str, code: str, message: str, retryable: bool) -> NewsResponse:
    error: ErrorDetail = {
        "service": SERVICE_NAME,
        "code": code,
        "message": message,
        "retryable": retryable,
    }
    return {"request_id": str(uuid4()), "status": status, "error": error}


def _clean_text(raw: str) -> str:
    return unescape(_TAG_RE.sub("", raw)).strip()


def _parse_published_at(raw: str) -> str | None:
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _relevance(company_name: str, headline: str, summary: str) -> str:
    haystack = f"{headline} {summary}"
    return "high" if company_name in haystack else "low"


def map_upstream_response(
    payload: dict[str, Any],
    request: NewsRequest,
    now: datetime | None = None,
) -> NewsResponse:
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=request["lookback_days"])
    seen: set[str] = set()
    articles: list[Article] = []

    for item in payload.get("items", []):
        headline = _clean_text(item.get("title", ""))
        summary = _clean_text(item.get("description", ""))
        source_url = item.get("originallink") or item.get("link") or ""
        dedupe_key = source_url or headline
        if not dedupe_key or dedupe_key in seen:
            continue

        relevance = _relevance(request["company_name"], headline, summary)
        if relevance == "low":
            continue

        published_at = _parse_published_at(item.get("pubDate", ""))
        if published_at and published_at < cutoff.isoformat().replace("+00:00", "Z"):
            continue

        seen.add(dedupe_key)
        articles.append(
            {
                "headline": headline,
                "publisher": item.get("publisher") or "unknown",
                "published_at": published_at or "",
                "summary": summary,
                "source_url": source_url,
                "relevance": relevance,
            }
        )
        if len(articles) >= request["limit"]:
            break

    status = "success" if articles else "no_data"
    return {
        "request_id": str(uuid4()),
        "status": status,
        "company_name": request["company_name"],
        "stock_code": request["stock_code"],
        "articles": articles,
        "result_count": len(articles),
        "collected_at": (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
    }


def fetch_news(
    request: NewsRequest,
    config: NewsConfig | None = None,
    client: NaverNewsClient | None = None,
) -> NewsResponse:
    active_config = config or get_config()
    if active_config.mock_enabled:
        return build_mock_news(request["company_name"], request["stock_code"])

    owns_client = client is None
    active_client = client or NaverNewsClient(
        active_config.api_url,
        active_config.client_id,
        active_config.client_secret,
        active_config.timeout_sec,
    )
    try:
        payload = active_client.search_news(request["company_name"], request["limit"])
        return map_upstream_response(payload, request)
    except NaverNewsAPITimeout:
        return error_response("timeout", "NEWS_API_TIMEOUT", "뉴스 조회가 시간 초과되었습니다.", True)
    except NaverNewsAPIUnauthorized:
        return error_response("unauthorized", "NEWS_API_UNAUTHORIZED", "뉴스 조회 인증에 실패했습니다.", False)
    except NaverNewsAPIUnavailable:
        return error_response("external_api_error", "NEWS_API_UNAVAILABLE", "뉴스를 일시적으로 가져오지 못했습니다.", True)
    finally:
        if owns_client:
            active_client.close()
