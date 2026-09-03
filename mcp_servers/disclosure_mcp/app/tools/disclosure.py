"""Disclosure MCP의 세 공개 Tool 등록과 오류 경계."""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from uuid import uuid4

from fastmcp import FastMCP

from app.clients.dart import DartApiError, DartClient, DartTimeoutError, DartUnavailableError
from app.clients.embedding import EmbeddingError, EmbeddingRateLimitError, OpenAIEmbeddingClient
from app.clients.repository import DisclosureRepository
from app.core.config import DisclosureConfig, get_config
from app.core.errors import ConfigurationError
from app.rag import ReportStore
from app.services.annual_report import AnnualReportNotFoundError, AnnualReportService
from app.services.company import CompanyResolver, UnsupportedCompanyError
from app.services.disclosure import DisclosureService
from app.services.document import DocumentParseError, DocumentService


def register_disclosure_tools(mcp: FastMCP) -> None:
    """FastMCP 인스턴스에 팀 계약의 세 Tool만 등록한다."""

    @mcp.tool()
    def get_recent_disclosures(
        stock_code: str,
        company_name: str | None = None,
        lookback_days: int = 30,
        limit: int = 20,
    ) -> dict[str, Any]:
        """최근 공시 제목·접수번호·DART URL 목록을 반환한다."""

        try:
            result = dict(
                _recent_service().get_recent_disclosures(
                    stock_code=stock_code,
                    company_name=company_name,
                    lookback_days=lookback_days,
                    limit=limit,
                )
            )
            result.update(_common_fields(stock_code=stock_code, company_name=company_name))
            return result
        except Exception as error:  # Tool 경계에서는 내부 예외를 노출하지 않는다.
            return _tool_error(error)

    @mcp.tool()
    def get_disclosure_detail(receipt_number: str) -> dict[str, Any]:
        """공시 원문을 표 평탄화한 뒤 앞 3,000자까지만 반환한다."""

        try:
            result = dict(_document_service().get_disclosure_detail(receipt_number))
            result.update(_common_fields())
            return result
        except Exception as error:
            return _tool_error(error)

    @mcp.tool()
    def search_annual_report(
        stock_code: str,
        query: str,
        company_name: str | None = None,
        top_k: int = 5,
        report_year: int | None = None,
    ) -> dict[str, Any]:
        """사업보고서의 관련 원문 청크를 최대 다섯 개 반환한다."""

        try:
            result = dict(
                _annual_service().search_annual_report(
                    stock_code=stock_code,
                    query=query,
                    company_name=company_name,
                    top_k=top_k,
                    report_year=report_year,
                )
            )
            result.update(_common_fields(stock_code=stock_code, company_name=company_name))
            return result
        except Exception as error:
            return _tool_error(error)


@lru_cache(maxsize=1)
def _config() -> DisclosureConfig:
    return get_config()


@lru_cache(maxsize=1)
def _repository() -> DisclosureRepository:
    config = _config()
    if not config.database_url:
        raise ConfigurationError("DATABASE_URL is required.")
    return DisclosureRepository(config.database_url)


@lru_cache(maxsize=1)
def _dart_client() -> DartClient:
    return DartClient(_config())


@lru_cache(maxsize=1)
def _recent_service() -> DisclosureService:
    repository = _repository()
    return DisclosureService(
        company_resolver=CompanyResolver(repository),
        dart_client=_dart_client(),
        repository=repository,
    )


@lru_cache(maxsize=1)
def _document_service() -> DocumentService:
    return DocumentService(dart_client=_dart_client(), repository=_repository())


@lru_cache(maxsize=1)
def _annual_service() -> AnnualReportService:
    config = _config()
    config.validate_for_annual_report_search()
    assert config.database_url is not None
    return AnnualReportService(
        company_resolver=CompanyResolver(_repository()),
        dart_client=_dart_client(),
        embedding_client=OpenAIEmbeddingClient(config),
        report_store=ReportStore(config.database_url),
    )


def _common_fields(
    *, stock_code: str | None = None, company_name: str | None = None
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "request_id": str(uuid4()),
        "source_type": "dart",
    }
    if stock_code is not None:
        fields["stock_code"] = stock_code
    if company_name is not None:
        fields["company_name"] = company_name
    return fields


def _tool_error(error: Exception) -> dict[str, Any]:
    status, code, message, retryable = _error_details(error)
    return {
        **_common_fields(),
        "status": status,
        "error": {
            "service": "disclosure_mcp",
            "code": code,
            "message": message,
            "retryable": retryable,
        },
    }


def _error_details(error: Exception) -> tuple[str, str, str, bool]:
    if isinstance(error, UnsupportedCompanyError):
        return "unsupported_company", "UNSUPPORTED_COMPANY", str(error), False
    if isinstance(error, (ValueError, ConfigurationError, DocumentParseError)):
        return "invalid_request", "INVALID_REQUEST", "요청값을 확인해 주세요.", False
    if isinstance(error, AnnualReportNotFoundError):
        return "no_data", "NO_DATA", "조회 가능한 사업보고서가 없습니다.", False
    if isinstance(error, DartTimeoutError):
        return "timeout", "DART_TIMEOUT", "DART 응답 시간이 초과되었습니다.", True
    if isinstance(
        error,
        (DartApiError, DartUnavailableError, EmbeddingError, EmbeddingRateLimitError),
    ):
        return "external_api_error", "EXTERNAL_API_ERROR", "외부 서비스 호출에 실패했습니다.", True
    return "internal_error", "INTERNAL_ERROR", "서버 내부 오류가 발생했습니다.", False
