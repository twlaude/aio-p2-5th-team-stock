# Backend ↔ MCP Client 분석 계약

## 연결

- 주소: `POST http://MCP_CLIENT_HOST:8010/internal/v1/common-analyses`
- 방식: HTTP REST + JSON
- 시간 제한: Backend 75초, MCP Client Workflow 60초
- 사용자 ID, 로그인 토큰, 아이디·비밀번호, 대화 전체는 전송하지 않는다.
- 회원 요청은 투자 성향 네 값을 함께 보낸다. 비회원은 `investment_profile`을 `null`로 보낸다.

## 요청 (회원)

```json
{
  "request_id": "uuid",
  "company": {
    "company_name": "삼성전자",
    "stock_code": "005930"
  },
  "investment_profile": {
    "experience_level": "beginner",
    "risk_profile": "balanced",
    "investment_horizon": "long",
    "preferred_evidence": "news"
  },
  "requested_at": "2026-09-01T09:00:00Z"
}
```

## 요청 (비회원)

```json
{
  "request_id": "uuid",
  "company": {
    "company_name": "삼성전자",
    "stock_code": "005930"
  },
  "investment_profile": null,
  "requested_at": "2026-09-01T09:00:00Z"
}
```

Backend가 지원 기업을 검증한 뒤 호출하므로 MCP Client는 정식 기업명과 6자리 종목 코드를 받는다. MCP Client가 받은 투자 성향은 Price·News·Disclosure·Community MCP에는 전달하지 않는다.

이 서비스는 자유 질문형이 아니므로 MCP Client 요청에 `question`, `date_range`를 포함하지 않는다.

## 성공 또는 부분 성공 응답

```json
{
  "request_id": "uuid",
  "run_id": "uuid",
  "status": "success",
  "termination_reason": "completed",
  "company": {
    "company_name": "삼성전자",
    "stock_code": "005930"
  },
  "price": {
    "current_price": 0,
    "change": 0,
    "change_rate": 0.0,
    "as_of": "2026-09-01T06:30:00Z",
    "source_name": "한국투자증권 Open API"
  },
  "common_analysis": {
    "one_line_summary": "추천 없이 현재 상황을 설명하는 한 줄",
    "market_temperature": {
      "score": 72,
      "label": "관심 높음",
      "data_coverage": ["price", "news", "community"]
    },
    "evidence_level": {
      "level": "high",
      "reason": "공식 근거 확인 수준에 대한 설명"
    },
    "news_summary": "뉴스 요약",
    "disclosure_summary": "공시 요약",
    "community_summary": "커뮤니티 요약"
  },
  "personalized_checkpoints": {
    "personal_summary": "회원 성향에 맞춘 한 줄 해석",
    "priority_checks": ["확인 항목 1", "확인 항목 2"],
    "caution": "주의할 점 1개"
  },
  "sources": [],
  "partial_failures": [],
  "trace_summary": {
    "tool_calls": 5,
    "llm_calls": 1,
    "completed_tools": ["get_stock_quote", "search_news"],
    "failed_tools": [],
    "duration_ms": 1200
  },
  "collected_at": "2026-09-01T09:00:10Z"
}
```

`personalized_checkpoints`는 요청에 `investment_profile`이 있을 때만 채운다. 비회원 요청(`investment_profile: null`)에는 이 필드를 생략하거나 `null`로 반환한다.

## MCP Client 책임

1. Price·News·Disclosure·Community MCP의 기본 Tool을 병렬로 호출한다.
2. 외부 원본 API를 직접 호출하거나 원본 데이터를 저장하지 않는다.
3. 뉴스 최대 5건, 연관 보고서 청크 3~5개, 커뮤니티 집계 결과만 LLM에 전달한다.
4. 시장 관심 온도와 근거 확인 정도는 확정 규칙으로 계산하고 LLM은 이를 설명한다.
5. Agent 최대 단계는 3으로 제한한다.
6. 일부 Tool 실패 시 성공한 자료를 유지하고 `partial_success`로 반환한다.
7. `investment_profile`을 받으면 공통 분석과 성향 네 값으로 `personalized_checkpoints`를 OpenAI `gpt-5.6-luna`로 생성한다. 이 값은 Price·News·Disclosure·Community MCP에 전달하지 않는다.
8. 기본 조회는 AI가 선택하지 않는다. Luna Agent에는 최근 공시 상세 조회 Tool만 허용하고, 기본 조회에 포함된 접수번호를 최대 2건까지 사용할 수 있다.

## 종료 이유

```text
completed
no_data
partial_completed
model_error
invalid_tool_call
mcp_tool_error
max_steps_exceeded
workflow_timeout
```
