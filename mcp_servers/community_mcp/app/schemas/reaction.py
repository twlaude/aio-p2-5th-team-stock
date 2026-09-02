from typing import Any, Literal, TypedDict

Status = Literal["success", "partial_success", "no_data", "unsupported_company", "invalid_request", "unauthorized", "external_api_error", "timeout", "internal_error"]
FGIStatus = Literal["success", "no_data", "unsupported_company", "error"]
SampleStatus = Literal["sufficient", "insufficient_sample", "no_data"]


class ReactionRequest(TypedDict):
    company_name: str
    stock_code: str
    lookback_days: int
    limit: int


class FGIRequest(TypedDict):
    company_name: str
    stock_code: str


class ErrorDetail(TypedDict):
    service: str
    code: str
    message: str
    retryable: bool


class ReactionResponse(TypedDict, total=False):
    request_id: str
    status: Status
    sample_status: SampleStatus
    company_name: str
    stock_code: str
    period: dict[str, Any]
    sample_size: int
    sentiment: dict[str, int]
    top_topics: dict[str, list[str]]
    representative_evidence: list[dict[str, str]]
    source_name: str
    source_detail: str
    collected_at: str
    fgi_mean: float
    fgi_latest: dict[str, Any] | None
    note: str
    supported_codes: list[str]
    mock: bool
    error: ErrorDetail


FGIResponse = dict[str, Any]
