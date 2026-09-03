from app.schemas.news import NewsResponse


def build_mock_news(company_name: str, stock_code: str) -> NewsResponse:
    return {
        "status": "success",
        "company_name": company_name,
        "stock_code": stock_code,
        "articles": [
            {
                "headline": f"{company_name}, 실적 개선 기대감에 강세",
                "publisher": "mock 경제신문",
                "published_at": "2026-09-01T01:00:00Z",
                "summary": "업황 회복과 수요 증가로 실적 개선 기대가 커지고 있다.",
                "source_url": "https://example.com/news/1",
                "relevance": "high",
            },
            {
                "headline": f"{company_name} 관련 업계 동향 점검",
                "publisher": "mock 산업일보",
                "published_at": "2026-08-31T05:30:00Z",
                "summary": "업계 전반의 공급망 이슈와 대응 현황을 정리했다.",
                "source_url": "https://example.com/news/2",
                "relevance": "medium",
            },
            {
                "headline": f"{company_name}, 신규 사업 발표",
                "publisher": "mock 테크뉴스",
                "published_at": "2026-08-30T09:15:00Z",
                "summary": "신규 사업 영역 진출 계획을 공개했다.",
                "source_url": "https://example.com/news/3",
                "relevance": "high",
            },
        ],
        "result_count": 3,
        "collected_at": "2026-09-01T09:00:00Z",
        "mock": True,
    }
