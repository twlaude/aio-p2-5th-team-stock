"""사업보고서 수집·색인·검색 서비스."""

from __future__ import annotations

from datetime import datetime, timezone
import re

from app.clients.dart import DartApiError, DartClient
from app.clients.embedding import OpenAIEmbeddingClient
from app.rag import ReportStore, chunk_sections, parse_report_sections
from app.schemas.re import DartPeriodicReportType
from app.schemas.search import AnnualReportSearchResponse, MatchedPassage
from app.services.company_resolver import CompanyResolver


class AnnualReportNotFoundError(LookupError):
    """요청한 사업연도의 DART 사업보고서를 찾지 못했다."""


class AnnualReportService:
    """미색인 사업보고서는 한 번 수집하고 이후 DB 결과를 재사용한다."""

    def __init__(
        self,
        *,
        company_resolver: CompanyResolver,
        dart_client: DartClient,
        embedding_client: OpenAIEmbeddingClient,
        report_store: ReportStore,
    ) -> None:
        self._company_resolver = company_resolver
        self._dart_client = dart_client
        self._embedding_client = embedding_client
        self._report_store = report_store

    def ingest_periodic_report(
        self,
        *,
        stock_code: str,
        report_year: int,
        report_type: DartPeriodicReportType,
    ) -> None:
        """DART의 최신 정정본을 기준으로 기업·연도 정기보고서를 다시 색인한다."""

        company = self._company_resolver.resolve(stock_code=stock_code)
        candidates = self._dart_client.get_periodic_reports(
            corp_code=company["corp_code"],
            begin_date=f"{report_year}0101",
            end_date=f"{report_year + 1}0630",
            report_type=report_type,
        )
        candidates = [
            candidate
            for candidate in candidates
            if _report_year(candidate["report_nm"], report_type) == report_year
        ]
        candidates.sort(key=lambda candidate: candidate["rcept_no"], reverse=True)
        if not candidates:
            raise AnnualReportNotFoundError(f"{report_year} {report_type} 보고서가 없습니다.")

        for candidate in candidates:
            try:
                document = self._dart_client.get_document(candidate["rcept_no"])
            except DartApiError as error:
                if error.status == "014":
                    continue
                raise
            chunks = chunk_sections(parse_report_sections(document["xml"]))
            if not chunks:
                raise AnnualReportNotFoundError("색인 가능한 사업보고서 섹션이 없습니다.")
            embeddings = self._embedding_client.embed([chunk.content for chunk in chunks])
            self._report_store.replace_report(
                stock_code=company["stock_code"],
                report_year=report_year,
                report_type=report_type,
                report_name=candidate["report_nm"],
                receipt_number=candidate["rcept_no"],
                published_at=_published_at(candidate["rcept_dt"]),
                source_url=_source_url(candidate["rcept_no"]),
                chunks=chunks,
                embeddings=embeddings,
                embedding_model=self._embedding_client.model,
            )
            return
        raise AnnualReportNotFoundError("원문을 내려받을 수 있는 사업보고서가 없습니다.")

    def ingest_annual_report(self, *, stock_code: str, report_year: int) -> None:
        """기존 호출부 호환용 사업보고서 색인 래퍼."""

        self.ingest_periodic_report(
            stock_code=stock_code, report_year=report_year, report_type="annual"
        )

    def search_annual_report(
        self,
        *,
        stock_code: str,
        query: str,
        company_name: str | None = None,
        top_k: int = 5,
        report_year: int | None = None,
    ) -> AnnualReportSearchResponse:
        if not query.strip():
            raise ValueError("query는 비어 있을 수 없습니다.")
        if not 1 <= top_k <= 5:
            raise ValueError("top_k는 1~5여야 합니다.")
        company = self._company_resolver.resolve(
            stock_code=stock_code, company_name=company_name
        )
        return self.search_periodic_report(
            stock_code=company["stock_code"],
            query=query,
            company_name=company["company_name"],
            top_k=top_k,
            report_year=report_year,
            report_type="annual",
        )

    def search_periodic_report(
        self,
        *,
        stock_code: str,
        query: str,
        company_name: str | None = None,
        top_k: int = 5,
        report_year: int | None = None,
        report_type: DartPeriodicReportType,
    ) -> AnnualReportSearchResponse:
        """사업·반기·분기보고서 중 지정한 유형의 관련 원문을 검색한다."""

        if not query.strip():
            raise ValueError("query는 비어 있을 수 없습니다.")
        if not 1 <= top_k <= 5:
            raise ValueError("top_k는 1~5여야 합니다.")
        company = self._company_resolver.resolve(
            stock_code=stock_code, company_name=company_name
        )
        target_year = report_year or _default_report_year(report_type)
        report = self._report_store.get_report(
            company["stock_code"], report_type, target_year
        )
        if report is None:
            self.ingest_periodic_report(
                stock_code=company["stock_code"],
                report_year=target_year,
                report_type=report_type,
            )
            report = self._report_store.get_report(
                company["stock_code"], report_type, target_year
            )
        assert report is not None
        query_embedding = self._embedding_client.embed([query])[0]
        hits = self._report_store.search(
            report_id=report.id, query_embedding=query_embedding, top_k=top_k
        )
        passages: list[MatchedPassage] = [
            {
                "section": hit.section_title,
                "text": hit.content,
                "score": round(hit.score, 6),
                "match_type": "vector",
            }
            for hit in hits
        ]
        return {
            "status": "success" if passages else "no_data",
            "report_name": report.report_name,
            "receipt_number": report.receipt_number,
            "report_year": report.report_year,
            "report_type": report.report_type,
            "matched_passages": passages,
            "available_years": self._report_store.available_years(
                company["stock_code"], report_type
            ),
            "source_url": report.source_url,
            "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


def _report_year(
    report_name: str, report_type: DartPeriodicReportType
) -> int | None:
    month = {"annual": "12", "semi_annual": "06", "quarterly": "03|09"}[report_type]
    match = re.search(rf"\((\d{{4}})\.(?:{month})\)", report_name)
    return int(match.group(1)) if match else None


def _published_at(dart_date: str) -> datetime:
    return datetime.strptime(dart_date, "%Y%m%d").replace(tzinfo=timezone.utc)


def _source_url(receipt_number: str) -> str:
    return f"https://dart.fss.or.kr/dsaf001/main.do?rcptNo={receipt_number}"


def _default_report_year(report_type: DartPeriodicReportType) -> int:
    now = datetime.now()
    if report_type == "annual":
        return now.year - 1
    if report_type == "semi_annual":
        return now.year if now.month >= 8 else now.year - 1
    return now.year if now.month >= 5 else now.year - 1
