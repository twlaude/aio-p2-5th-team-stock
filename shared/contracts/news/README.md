# News MCP Tool 계약

## 연결과 Tool

- MCP 주소: `http://NEWS_MCP_HOST:8021/mcp`
- Tool 이름: `search_news`
- 실제 제공처: NAVER API HUB 뉴스 검색 API
- 기본 조회: 최근 자료 우선 최대 10건, MCP Client가 중복 제거 결과 중 핵심 5건만 LLM에 사용

## 입력

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930",
  "lookback_days": 7,
  "limit": 10
}
```

`lookback_days`는 기본 7, `limit`은 최대 10이다.

## 출력

```json
{
  "status": "success",
  "company_name": "삼성전자",
  "stock_code": "005930",
  "articles": [
    {
      "headline": "기사 제목",
      "publisher": "언론사",
      "published_at": "2026-09-01T01:00:00Z",
      "summary": "검색 API가 제공한 짧은 설명",
      "source_url": "https://example.com/news/1",
      "relevance": "high"
    }
  ],
  "result_count": 1,
  "collected_at": "2026-09-01T09:00:00Z"
}
```

본문 전체 크롤링은 MVP 범위에서 제외한다. 회사와 관련 없는 기사 및 URL·제목이 같은 기사는 제거한다.
