import asyncio
from datetime import datetime, timezone

from fastmcp import FastMCP

from app.rag.store import SearchHit, StoredReport
from app.services.annual_report_service import AnnualReportService
from app.services.disclosure_service import DisclosureService
from app.tools import disclosure as disclosure_tools


def _record(receipt_number: str, report_name: str, published_at: str) -> dict:
    return {
        "corp_cls": "Y",
        "corp_name": "테스트",
        "corp_code": "00123456",
        "stock_code": "005930",
        "report_nm": report_name,
        "rcept_no": receipt_number,
        "flr_nm": "테스트",
        "rcept_dt": published_at,
        "rm": "",
    }


class FakeResolver:
    def resolve(self, *, stock_code: str, company_name: str | None = None) -> dict:
        return {
            "stock_code": stock_code,
            "company_name": company_name or "테스트",
            "corp_code": "00123456",
        }


class FakeDartClient:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses
        self.calls: list[str | None] = []

    def get_disclosures(self, **kwargs) -> dict:
        disclosure_type = kwargs["disclosure_type"]
        self.calls.append(disclosure_type)
        return self.responses.get(disclosure_type, {"status": "013", "list": []})


class FakeRepository:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def upsert_disclosures(self, rows: list[dict]) -> None:
        self.rows = rows


def _disclosure_service(
    responses: dict[str, dict],
) -> tuple[DisclosureService, FakeDartClient, FakeRepository]:
    dart = FakeDartClient(responses)
    repository = FakeRepository()
    service = DisclosureService(
        company_resolver=FakeResolver(),
        dart_client=dart,
        repository=repository,
    )
    return service, dart, repository


def test_recent_disclosures_defaults_to_one_periodic_request() -> None:
    service, dart, _ = _disclosure_service({"A": {"status": "013", "list": []}})

    result = service.get_recent_disclosures(stock_code="005930")

    assert result["status"] == "no_data"
    assert dart.calls == ["A"]


def test_recent_disclosures_merges_deduplicates_and_sorts_types() -> None:
    duplicate = _record("20260902000003", "단일판매ㆍ공급계약", "20260902")
    service, dart, repository = _disclosure_service(
        {
            "B": {
                "status": "000",
                "list": [
                    _record("20260901000002", "유상증자결정", "20260901"),
                    duplicate,
                ],
            },
            "I": {
                "status": "000",
                "list": [
                    duplicate,
                    _record("20260902000004", "조회공시요구", "20260902"),
                ],
            },
        }
    )

    result = service.get_recent_disclosures(
        stock_code="005930", disclosure_types=["B", "I"]
    )

    assert dart.calls == ["B", "I"]
    assert [item["receipt_number"] for item in result["disclosures"]] == [
        "20260902000004",
        "20260902000003",
        "20260901000002",
    ]
    assert len(repository.rows) == 3


def test_invalid_disclosure_type_returns_tool_error(monkeypatch) -> None:
    service, _, _ = _disclosure_service({})
    monkeypatch.setattr(disclosure_tools, "_recent_service", lambda: service)
    mcp = FastMCP("test-disclosure")
    disclosure_tools.register_disclosure_tools(mcp)

    result = asyncio.run(
        mcp.call_tool(
            "get_recent_disclosures",
            {"stock_code": "005930", "disclosure_types": ["b"]},
        )
    ).structured_content

    assert result["status"] == "invalid_request"
    assert result["error"]["code"] == "INVALID_REQUEST"


def test_recent_disclosures_exposes_existing_category_as_kind() -> None:
    service, _, _ = _disclosure_service(
        {
            "A": {
                "status": "000",
                "list": [_record("20260903000001", "분기보고서", "20260903")],
            },
            "B": {
                "status": "000",
                "list": [_record("20260903000002", "단일판매ㆍ공급계약", "20260903")],
            },
            "E": {
                "status": "000",
                "list": [_record("20260903000003", "기업설명회(IR)개최", "20260903")],
            },
        }
    )

    result = service.get_recent_disclosures(
        stock_code="005930", disclosure_types=["A", "B", "E"]
    )

    assert {
        item["report_name"]: item["disclosure_kind"] for item in result["disclosures"]
    } == {
        "분기보고서": "periodic",
        "단일판매ㆍ공급계약": "major",
        "기업설명회(IR)개최": "other",
    }


class FakeEmbeddingClient:
    model = "test"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] for _ in texts]


class FakeReportStore:
    report = StoredReport(
        id=1,
        stock_code="005930",
        report_year=2025,
        report_type="annual",
        report_name="사업보고서 (2025.12)",
        receipt_number="20260301000001",
        published_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        source_url="https://dart.fss.or.kr/test",
    )

    def get_report(
        self, stock_code: str, report_type: str, report_year: int | None = None
    ):
        return self.report

    def search(self, **kwargs) -> list[SearchHit]:
        return [
            SearchHit("고득점", "첫 번째", 0.8),
            SearchHit("경계값", "두 번째", 0.7),
            SearchHit("저득점", "세 번째", 0.4),
        ]

    def available_years(self, stock_code: str, report_type: str) -> list[int]:
        return [2025]


def _annual_service() -> AnnualReportService:
    return AnnualReportService(
        company_resolver=FakeResolver(),
        dart_client=FakeDartClient({}),
        embedding_client=FakeEmbeddingClient(),
        report_store=FakeReportStore(),
    )


def test_annual_report_min_score_filters_and_counts() -> None:
    service = _annual_service()
    result = service.search_annual_report(
        stock_code="005930", query="사업", min_score=0.7
    )

    assert result["status"] == "success"
    assert [passage["score"] for passage in result["matched_passages"]] == [0.8, 0.7]
    assert result["filtered_out"] == 1

    all_filtered = service.search_annual_report(
        stock_code="005930", query="사업", min_score=0.9
    )
    assert all_filtered["status"] == "success"
    assert all_filtered["matched_passages"] == []
    assert all_filtered["filtered_out"] == 3


def test_invalid_min_score_returns_tool_error(monkeypatch) -> None:
    monkeypatch.setattr(disclosure_tools, "_annual_service", _annual_service)
    mcp = FastMCP("test-disclosure")
    disclosure_tools.register_disclosure_tools(mcp)

    result = asyncio.run(
        mcp.call_tool(
            "search_annual_report",
            {"stock_code": "005930", "query": "사업", "min_score": 1.1},
        )
    ).structured_content

    assert result["status"] == "invalid_request"
    assert result["error"]["code"] == "INVALID_REQUEST"
