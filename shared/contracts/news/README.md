# News MCP Tool 계약

## 연결과 Tool

- MCP 주소: `http://NEWS_MCP_HOST:8021/mcp`
- Tool 이름: `search_news`
- 실제 제공처: NAVER API HUB 뉴스 검색 API
- 기본 조회: 최근 자료 우선 10건(요청 시 최대 100건), MCP Client가 중복 제거 결과 중 핵심 5건만 LLM에 사용

## 입력

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930",
  "lookback_days": 7,
  "limit": 10
}
```

`lookback_days`는 기본 7, `limit`은 기본 10이고 최대 100이다. 이는 네이버 뉴스 검색 API의 `display` 최대값과 같다.

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
  "relevant_count": 1,
  "collected_at": "2026-09-01T09:00:00Z"
}
```

`result_count`는 실제 반환한 기사 수다. `relevant_count`는 검색 API가 반환한 범위에서 lookback 기간 안에 있고,
회사명이 제목 또는 요약에 포함되어 관련도가 `high`인 중복 제거 기사 수다.

본문 전체 크롤링은 MVP 범위에서 제외한다. 회사와 관련 없는 기사 및 URL·제목이 같은 기사는 제거한다.
