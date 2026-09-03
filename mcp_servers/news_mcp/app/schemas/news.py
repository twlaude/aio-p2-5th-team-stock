from typing import Literal, TypedDict

Status = Literal[
    "success",
    "no_data",
    "invalid_request",
    "unauthorized",
    "external_api_error",
    "timeout",
    "internal_error",
]
Relevance = Literal["high", "medium", "low"]


class NewsRequest(TypedDict):
    company_name: str
    stock_code: str
    lookback_days: int
    limit: int


class ErrorDetail(TypedDict):
    service: str
    code: str
    message: str
    retryable: bool


class Article(TypedDict):
    headline: str
    publisher: str
    published_at: str
    summary: str
    source_url: str
    relevance: Relevance


class NewsResponse(TypedDict, total=False):
    request_id: str
    status: Status
    company_name: str
    stock_code: str
    articles: list[Article]
    result_count: int
    collected_at: str
    mock: bool
    error: ErrorDetail
