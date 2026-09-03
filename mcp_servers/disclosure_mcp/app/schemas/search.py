"""OpenDART 공시와 사업보고서 검색에 사용하는 스키마.

공개 Tool의 필드명은 shared/contracts/disclosure/README.md를 기준으로 한다.
"""

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
DocumentType = Literal["disclosure", "annual_report"]


class ErrorDetail(TypedDict):
    """실패 시 공통으로 반환하는 오류 정보."""

    service: str
    code: str
    message: str
    retryable: bool


class CompanyIdentity(TypedDict):
    """기업 식별 정보. corp_code는 MCP 외부에 노출하지 않는다."""

    company_name: str
    stock_code: str
    corp_code: str


class DisclosureItem(TypedDict):
    """최근 공시 목록의 한 항목."""

    report_name: str
    receipt_number: str
    published_at: str
    document_type: Literal["disclosure"]
    source_url: str


class RecentDisclosuresRequest(TypedDict):
    """get_recent_disclosures 입력값."""

    company_name: str
    stock_code: str
    lookback_days: int
    limit: int


class RecentDisclosuresResponse(TypedDict, total=False):
    """get_recent_disclosures 응답값."""

    status: Status
    disclosures: list[DisclosureItem]
    collected_at: str
    error: ErrorDetail


class DisclosureDetailRequest(TypedDict):
    """get_disclosure_detail 입력값."""

    receipt_number: str


class DisclosureDetailResponse(TypedDict, total=False):
    """get_disclosure_detail 응답값."""

    status: Status
    report_name: str
    receipt_number: str
    published_at: str
    document_type: Literal["disclosure"]
    summary: str
    source_url: str
    collected_at: str
    error: ErrorDetail


class MatchedPassage(TypedDict):
    """사업보고서에서 검색된 공식 원문 구절."""

    section: str
    text: str
    score: float


class AnnualReportSearchRequest(TypedDict):
    """search_annual_report 입력값."""

    company_name: str
    stock_code: str
    query: str
    top_k: int


class AnnualReportSearchResponse(TypedDict, total=False):
    """search_annual_report 응답값."""

    status: Status
    report_name: str
    receipt_number: str
    report_year: int
    matched_passages: list[MatchedPassage]
    source_url: str
    collected_at: str
    error: ErrorDetail


class AnnualReportChunk(TypedDict):
    """RAG 저장소의 사업보고서 청크. 외부 Tool 응답에는 직접 노출하지 않는다."""

    company_name: str
    stock_code: str
    corp_code: str
    report_name: str
    receipt_number: str
    report_year: int
    published_at: str
    document_type: Literal["annual_report"]
    section: str
    text: str
    source_url: str
    collected_at: str
