"""최근 DART 공시 목록을 MCP 계약 형태로 정리하고 캐시한다."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.clients.dart import DartClient
from app.clients.repository import DisclosureCacheRow, DisclosureRepository
from app.schemas.re import DartDisclosureRecord
from app.schemas.search import DisclosureItem, RecentDisclosuresResponse
from app.services.company_resolver import CompanyResolver


_SEOUL = ZoneInfo("Asia/Seoul")
_DISCLOSURE_TYPES = frozenset("ABCDEFGHIJ")
_MAJOR_DISCLOSURE_TERMS = (
    "유상증자",
    "무상증자",
    "전환사채",
    "합병",
    "분할",
    "자기주식 취득",
    "자기주식 처분",
    "최대주주 변경",
    "단일판매ㆍ공급계약",
    "단일판매·공급계약",
    "단일판매공급계약",
    "소송",
    "영업정지",
)


class DisclosureService:
    """회사 식별, DART 조회, 공시 캐시를 하나의 흐름으로 조합한다."""

    def __init__(
        self,
        *,
        company_resolver: CompanyResolver,
        dart_client: DartClient,
        repository: DisclosureRepository,
    ) -> None:
        self._company_resolver = company_resolver
        self._dart_client = dart_client
        self._repository = repository

    def get_recent_disclosures(
        self,
        *,
        stock_code: str,
        company_name: str | None = None,
        lookback_days: int = 30,
        limit: int = 20,
        disclosure_types: list[str] | None = None,
    ) -> RecentDisclosuresResponse:
        """최근 공시를 최신순으로 반환하고, 조회한 목록을 DB에 저장한다."""

        requested_types = self._validate_request(lookback_days, limit, disclosure_types)
        company = self._company_resolver.resolve(
            stock_code=stock_code,
            company_name=company_name,
        )
        end_date = datetime.now(_SEOUL).date()
        begin_date = end_date - timedelta(days=lookback_days - 1)
        # 팀 결정(2026-09-04): 기본값은 정기공시(A)만 유지한다.
        records_by_receipt: dict[str, DartDisclosureRecord] = {}
        for disclosure_type in requested_types:
            raw_response = self._dart_client.get_disclosures(
                corp_code=company["corp_code"],
                begin_date=begin_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                page_count=100,
                disclosure_type=disclosure_type,
            )
            if raw_response["status"] == "013":
                continue
            for record in raw_response.get("list", []):
                records_by_receipt.setdefault(record["rcept_no"], record)
        collected_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if not records_by_receipt:
            return {"status": "no_data", "disclosures": [], "collected_at": collected_at}

        sorted_disclosures = sorted(
            records_by_receipt.values(),
            key=lambda record: (record["rcept_dt"], record["rcept_no"]),
            reverse=True,
        )
        cache_rows = [
            self._to_cache_row(record, company["stock_code"])
            for record in sorted_disclosures
        ]
        self._repository.upsert_disclosures(cache_rows)
        items = [self._to_disclosure_item(record) for record in sorted_disclosures[:limit]]
        return {"status": "success", "disclosures": items, "collected_at": collected_at}

    @staticmethod
    def _validate_request(
        lookback_days: int,
        limit: int,
        disclosure_types: list[str] | None,
    ) -> list[str]:
        if not 1 <= lookback_days <= 365:
            raise ValueError("lookback_days는 1~365여야 합니다.")
        if not 1 <= limit <= 100:
            raise ValueError("limit은 1~100이어야 합니다.")
        requested_types = ["A"] if disclosure_types is None else disclosure_types
        if not requested_types or any(
            not isinstance(value, str) or value not in _DISCLOSURE_TYPES
            for value in requested_types
        ):
            raise ValueError("disclosure_types는 A~J 대문자 목록이어야 합니다.")
        return list(dict.fromkeys(requested_types))

    @staticmethod
    def _source_url(receipt_number: str) -> str:
        return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_number}"

    @classmethod
    def _to_disclosure_item(cls, record: DartDisclosureRecord) -> DisclosureItem:
        return {
            "report_name": record["report_nm"],
            "receipt_number": record["rcept_no"],
            "published_at": cls._to_iso_datetime(record["rcept_dt"]),
            "document_type": "disclosure",
            "disclosure_kind": cls._category(record["report_nm"]),
            "source_url": cls._source_url(record["rcept_no"]),
        }

    @classmethod
    def _to_cache_row(
        cls, record: DartDisclosureRecord, stock_code: str
    ) -> DisclosureCacheRow:
        report_name = record["report_nm"]
        return {
            "receipt_number": record["rcept_no"],
            "stock_code": stock_code,
            "report_name": report_name,
            "published_at": cls._to_iso_datetime(record["rcept_dt"]),
            "filed_at": cls._to_date(record["rcept_dt"]),
            "category": cls._category(report_name),
            "is_major": cls._is_major(report_name),
            "is_correction": "정정" in report_name,
            "source_url": cls._source_url(record["rcept_no"]),
            "raw_payload": dict(record),
        }

    @staticmethod
    def _to_date(dart_date: str) -> str:
        return date.fromisoformat(
            f"{dart_date[:4]}-{dart_date[4:6]}-{dart_date[6:8]}"
        ).isoformat()

    @staticmethod
    def _is_major(report_name: str) -> bool:
        return any(term in report_name for term in _MAJOR_DISCLOSURE_TERMS)

    @classmethod
    def _category(cls, report_name: str) -> str:
        if any(name in report_name for name in ("사업보고서", "반기보고서", "분기보고서")):
            return "periodic"
        if cls._is_major(report_name):
            return "major"
        return "other"

    @classmethod
    def _to_iso_datetime(cls, dart_date: str) -> str:
        return f"{cls._to_date(dart_date)}T00:00:00Z"
