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
  "span_hours": 26.5,
  "oldest_relevant_at": "2026-09-03T03:30:00Z",
  "collected_at": "2026-09-01T09:00:00Z"
}
```

`result_count`는 실제 반환한 기사 수다. `relevant_count`는 검색 API가 반환한 범위에서 lookback 기간 안에 있고,
회사명이 제목 또는 요약에 포함되어 관련도가 `high`인 중복 제거 기사 수다.
`oldest_relevant_at`는 그 관련 기사 중 가장 오래된 발행 시각, `span_hours`는 거기서 지금까지 걸린 시간(시간 단위, 소수 2자리)이다.
MCP Client는 `relevant_count`와 `span_hours`로 "관련 기사 100건이 쌓이는 데 걸리는 시간"을 계산해 뉴스 관심 점수를 낸다. 관련 기사가 없거나 발행 시각을 알 수 없으면 둘 다 `null`이다.

본문 전체 크롤링은 MVP 범위에서 제외한다. 회사와 관련 없는 기사 및 URL·제목이 같은 기사는 제거한다.
