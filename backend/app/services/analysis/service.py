from datetime import datetime, timezone

from app.clients.mcp_client import client as mcp_client
from app.repositories import analysis_repository
from app.schemas.analysis import (
    AnalysisDetail,
    AnalysisResponse,
    CompanyRef,
    EvidenceLevel,
    MarketTemperature,
    PersonalizedCheckpoints,
    PriceSnapshot,
    UnsupportedCompanyResponse,
)
from app.schemas.user import CurrentUser
from app.services.analysis import companies
from app.services.profile import service as profile_service

UNSUPPORTED_MESSAGE = (
    "아직 이 기업의 분석 정보는 제공하지 않습니다. "
    "현재는 2026년 9월 1일 기준 코스피 시가총액 상위 20개 기업만 지원하고 있어요."
)
UNSUPPORTED_ACTIONS = ["지원 기업 20개 보기", "다른 종목 검색하기"]


def run_analysis(
    query: str, current_user: CurrentUser | None
) -> AnalysisResponse | UnsupportedCompanyResponse:
    company = companies.resolve_company(query)
    if company is None:
        return UnsupportedCompanyResponse(message=UNSUPPORTED_MESSAGE, actions=UNSUPPORTED_ACTIONS)

    company_name = company["company_name"]
    stock_code = company["stock_code"]

    profile = profile_service.get_profile(current_user.user_id) if current_user else None
    requested_at = datetime.now(timezone.utc)
    raw = mcp_client.fetch_common_analysis(company_name, stock_code, profile)
    common = raw["common_analysis"]

    response = AnalysisResponse(
        request_id=raw["request_id"],
        status=raw["status"],
        access_level="guest",
        requires_login=True,
        company=CompanyRef(company_name=company_name, stock_code=stock_code, supported=True),
        price=PriceSnapshot(**raw["price"]),
        one_line_summary=common["one_line_summary"],
    )

    if profile is not None:
        response.access_level = "member"
        response.requires_login = False
        response.detail = AnalysisDetail(
            market_temperature=MarketTemperature(**common["market_temperature"]),
            evidence_level=EvidenceLevel(**common["evidence_level"]),
            news_summary=common["news_summary"],
            disclosure_summary=common["disclosure_summary"],
            community_summary=common["community_summary"],
            sources=raw.get("sources", []),
        )
        if raw.get("personalized_checkpoints"):
            response.personalized_checkpoints = PersonalizedCheckpoints(**raw["personalized_checkpoints"])

    analysis_repository.save_run(
        request_id=response.request_id,
        user_id=current_user.user_id if current_user else None,
        company_name=company_name,
        stock_code=stock_code,
        access_level=response.access_level,
        status=response.status,
        one_line_summary=response.one_line_summary,
        sources=raw.get("sources", []),
        partial_failures=raw.get("partial_failures", []),
        personalized_checkpoints=raw.get("personalized_checkpoints"),
        requested_at=requested_at,
        collected_at=raw.get("collected_at"),
    )
    return response
