from typing import Any

from app.schemas.analysis import CollectedData


def collected_data() -> CollectedData:
    return CollectedData(
        price={
            "status": "success",
            "company_name": "삼성전자",
            "stock_code": "005930",
            "current_price": 70000,
            "change": 1700,
            "change_rate": 2.5,
            "as_of": "2026-09-04T01:00:00Z",
            "source_name": "한국투자증권 Open API",
        },
        news={
            "status": "success",
            "result_count": 5,
            "articles": [
                {
                    "headline": f"삼성전자 관련 뉴스 {index}",
                    "publisher": "example.com",
                    "published_at": "2026-09-04T00:00:00Z",
                    "summary": "테스트 뉴스",
                    "source_url": f"https://example.com/news/{index}",
                    "relevance": "high",
                }
                for index in range(5)
            ],
        },
        disclosures={
            "status": "success",
            "disclosures": [
                {
                    "report_name": "주요사항보고서",
                    "receipt_number": "202609040001",
                    "published_at": "2026-09-04T00:00:00Z",
                    "source_url": "https://dart.fss.or.kr/1",
                },
                {
                    "report_name": "기업설명회",
                    "receipt_number": "202609030001",
                    "published_at": "2026-09-03T00:00:00Z",
                    "source_url": "https://dart.fss.or.kr/2",
                },
            ],
        },
        annual_report={
            "status": "success",
            "report_name": "2025년 사업보고서",
            "source_url": "https://dart.fss.or.kr/annual",
            "matched_passages": [
                {"section": "사업의 내용", "text": "반도체 사업 관련 테스트", "score": 0.8}
            ],
        },
        community={
            "status": "success",
            "sample_status": "sufficient",
            "sample_size": 50,
            "sentiment": {"positive_count": 20, "neutral_count": 20, "negative_count": 10},
            "top_topics": {"expectations": ["신제품"], "concerns": ["업황"]},
            "representative_evidence": [],
            "fgi_latest": {"fgi": 75.0, "label": "탐욕"},
            "source_name": "태웅님 커뮤니티 서버",
        },
        completed_tools=[
            "get_stock_quote",
            "search_news",
            "get_recent_disclosures",
            "search_annual_report",
            "get_community_reaction",
        ],
    )


class FakeCollector:
    def __init__(self, data: CollectedData) -> None:
        self.data = data

    async def collect(self, company: Any, reporter: Any) -> CollectedData:
        return self.data


class FakeDisclosureClient:
    async def get_disclosure_detail(self, receipt_number: str) -> dict[str, Any]:
        return {"status": "success", "receipt_number": receipt_number, "content": "공시 상세"}
