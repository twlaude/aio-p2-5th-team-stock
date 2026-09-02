# Disclosure MCP Tool 계약

## 연결

- MCP 주소: `http://DISCLOSURE_MCP_HOST:8022/mcp`
- 제공처: OpenDART
- 최신 연간 사업보고서 1개는 미리 저장·임베딩한다.
- 최근 공시 목록은 검색 시점 기준 30일을 조회하고 필요한 상세 공시는 1~2건만 가져온다.

## Tool 1: `get_recent_disclosures`

입력:

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930",
  "lookback_days": 30,
  "limit": 20
}
```

출력 핵심 필드:

```json
{
  "status": "success",
  "disclosures": [
    {
      "report_name": "공시명",
      "receipt_number": "접수번호",
      "published_at": "2026-09-01T00:00:00Z",
      "document_type": "disclosure",
      "source_url": "https://dart.fss.or.kr/..."
    }
  ],
  "collected_at": "2026-09-01T09:00:00Z"
}
```

## Tool 2: `get_disclosure_detail`

입력은 `receipt_number` 하나이며, 공시 제목·핵심 내용·공식 URL을 반환한다. Agent는 최근 목록에서 질문과 관련된 공시 최대 2건에만 사용한다.

## Tool 3: `search_annual_report`

입력:

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930",
  "query": "반도체 사업의 주요 위험과 성장 계획",
  "top_k": 5
}
```

출력:

```json
{
  "status": "success",
  "report_name": "최신 사업보고서",
  "receipt_number": "접수번호",
  "report_year": 2025,
  "matched_passages": [
    {
      "section": "사업의 내용",
      "text": "질문과 관련된 보고서 일부",
      "score": 0.82
    }
  ],
  "source_url": "https://dart.fss.or.kr/...",
  "collected_at": "2026-09-01T09:00:00Z"
}
```

`top_k`는 최대 5다. 보고서 전체를 LLM에 전달하지 않는다.
