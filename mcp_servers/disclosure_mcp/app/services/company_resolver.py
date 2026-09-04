"""공개 Tool 호출 전에 지원 대상 기업을 안전하게 식별한다."""

from __future__ import annotations

from app.clients.repository import DisclosureRepository
from app.schemas.search import CompanyIdentity


class UnsupportedCompanyError(ValueError):
    """지원 목록에 없거나 입력한 기업명과 종목코드가 맞지 않는다."""


class CompanyResolver:
    """종목코드를 기준으로 DB의 DART corp_code를 찾는다."""

    def __init__(self, repository: DisclosureRepository) -> None:
        self._repository = repository

    def resolve(
        self, *, stock_code: str, company_name: str | None = None
    ) -> CompanyIdentity:
        """지원 종목을 확인하고 내부에서만 사용할 corp_code를 반환한다."""

        normalized_stock_code = stock_code.strip()
        if not normalized_stock_code.isdigit() or len(normalized_stock_code) != 6:
            raise UnsupportedCompanyError("종목코드는 6자리 숫자여야 합니다.")

        company = self._repository.find_supported_company(normalized_stock_code)
        if company is None:
            raise UnsupportedCompanyError("지원하지 않는 종목입니다.")

        normalized_name = company_name.strip() if company_name else None
        if normalized_name and normalized_name != company["company_name"]:
            raise UnsupportedCompanyError("기업명과 종목코드가 일치하지 않습니다.")

        return {
            "company_name": company["company_name"],
            "stock_code": company["stock_code"],
            "corp_code": company["corp_code"],
        }
