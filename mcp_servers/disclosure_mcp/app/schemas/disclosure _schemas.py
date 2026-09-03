from typing import Literal, TypedDict


Status = Literal[
    "success",
    "no_data",
    "unsupported_company",
    "invalid_request",
    "external_api_error",
    "timeout",
    "internal_error",
]


class ErrorDetail(TypedDict):
    service: str
    code: str
    message: str
    retryable: bool


class RecentDisclosuresRequest(TypedDict):
    company_name: str
    stock_code: str
    lookback_days: int
    limit: int


class DisclosureItem(TypedDict):
    report_name: str
    receipt_number: str
    published_at: str
    document_type: Literal["disclosure"]
    source_url: str


class RecentDisclosuresResponse(TypedDict, total=False):
    status: Status
    company_name: str
    stock_code: str
    disclosures: list[DisclosureItem]
    collected_at: str
    error: ErrorDetail


class DisclosureDetailRequest(TypedDict):
    receipt_number: str


class DisclosureDetailResponse(TypedDict, total=False):
    status: Status
    report_name: str
    receipt_number: str
    published_at: str
    document_type: Literal["disclosure"]
    summary: str
    source_url: str
    collected_at: str
    error: ErrorDetail


class AnnualReportSearchRequest(TypedDict):
    company_name: str
    stock_code: str
    query: str
    top_k: int


class MatchedPassage(TypedDict):
    section: str
    text: str
    score: float


class AnnualReportSearchResponse(TypedDict, total=False):
    status: Status
    company_name: str
    stock_code: str
    report_name: str
    receipt_number: str
    report_year: int
    document_type: Literal["annual_report"]
    matched_passages: list[MatchedPassage]
    source_url: str
    collected_at: str
    error: ErrorDetail