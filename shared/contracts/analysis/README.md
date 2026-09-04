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
    "source_name": "한국투자증권 Open API",
    "volume_basis": "last_session",
    "volume_as_of": "2026-08-31"
  },
  "common_analysis": {
    "one_line_summary": "추천 없이 현재 상황을 설명하는 한 줄",
    "market_temperature": {
      "score": 72,
      "label": "관심 높음",
      "data_coverage": ["price", "news", "community"],
      "components": {
        "volume_activity": 24,
        "news_attention": 18,
        "community_activity": 15,
        "fear_greed_intensity": 15
      },
      "weight_covered": 100
    },
    "evidence_level": {
      "level": "high",
      "reason": "현재 이슈가 8월 29일 주요 공시와 맞아요",
      "matched": [
        {
          "issue": "현재 이슈",
          "report_name": "주요 공시",
          "receipt_number": "20260829000123",
          "published_at": "2026-08-29T00:00:00Z"
        }
      ],
      "unmatched": [],
      "material_count": 1
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
    "tool_calls": 6,
    "llm_calls": 1,
    "completed_tools": ["get_stock_quote", "search_news"],
    "failed_tools": [],
    "duration_ms": 1200
  },
  "collected_at": "2026-09-01T09:00:10Z"
}
```

`personalized_checkpoints`는 요청에 `investment_profile`이 있을 때만 채운다. 비회원 요청(`investment_profile: null`)에는 이 필드를 생략하거나 `null`로 반환한다.
`price.volume_basis`와 `price.volume_as_of`는 Price MCP가 선택한 거래량 기준과 기준 거래일을 전달한다. 구버전 Price 응답이나 일봉 실패에서는 두 필드를 생략하거나 `null`로 반환한다.

## 시장 관심 온도 v2

시장 관심 온도는 주가의 상승 가능성이나 매수 점수가 아니라, 거래량·뉴스·커뮤니티 활동이 평소보다 얼마나 활발한지와 공포탐욕 강도를 나타낸다. 각 항목은 다음 규칙으로 0~1 사이로 정규화한 뒤 배점을 곱한다.

| `components` key | 입력 | 정규화 | 배점 |
|---|---|---:|---:|
| `volume_activity` | `price.volume_ratio_20d`, 없으면 `1 + volume_change_rate / 100` | `clamp(ratio / 3, 0, 1)` | 30 |
| `news_attention` | `news.relevant_count`(없으면 `result_count`) + `news.span_hours` | 관련 기사 100건이 쌓이는 시간 `h = span_hours × 100 / count`. 6시간 이하 1, 168시간(7일) 이상 0, 사이는 로그 스케일. `span_hours` 없으면 `clamp(count / 80, 0, 1)` 폴백 | 25 |
| `community_activity` | `community.activity.ratio` | `clamp(ratio / 3, 0, 1)` | 25 |
| `fear_greed_intensity` | `community.fgi_latest.fgi` | `abs(fgi - 50) / 50` | 20 |

출처의 `status`가 `success`가 아니거나 입력값이 없으면 해당 항목은 미가용으로 처리하고 `components`에서 생략한다. 최종 `score`는 `round(가용 항목 점수 합 / 가용 항목 배점 합 * 100)`으로 재정규화하며, 가용 배점이 없으면 0이다. `weight_covered`는 가용 항목의 배점 합으로 0~100이다. `data_coverage`와 `label` 구간은 기존 의미를 유지한다.

## 공시 근거 v2

`evidence_level`은 자료 종류 수가 아니라 커뮤니티 중심의 현재 이슈와 최근 30일 주요 비정기 공시의 직접 연결 여부로 정한다. 뉴스 이슈는 제목에 정식 회사명이 포함된 기사만 보조로 사용하며 임베딩·유사도 점수는 쓰지 않는다.

| 단계 | 판정 |
|---|---|
| `high` | 규칙 사전으로 현재 이슈와 연결된 주요 공시가 1건 이상 |
| `medium` | 연결 공시는 없지만 최근 30일 주요 공시가 1건 이상 |
| `low` | 최근 30일 주요 공시가 없음 |
| `low` (실패) | 주요 비정기 공시 조회 상태가 `success` 또는 `no_data`가 아님 |

`evidence_level.matched[]`는 `issue`, `report_name`, `receipt_number`, `published_at`을 담고, `unmatched[]`는 공시와 연결되지 않은 현재 이슈, `material_count`는 최근 30일 주요 공시 수다. `sources[]`의 공시 메타는 연결된 이슈를 `confirmed`, 미연결 이슈를 첫 공시 source의 `unconfirmed`에 중복 없이 싣고, `disclosure_kind`를 `major`, `periodic`, `other` 중 하나로 표시한다. 공시 source는 연결 주요 공시, 나머지 주요 공시 최대 1건, 정기공시 최대 1건, 사업보고서 순서이며 총 4건 이하다.

## MCP Client 책임

1. Price·News·Disclosure·Community MCP의 여섯 기본 Tool(정기공시와 주요 비정기 공시 조회 포함)을 병렬로 호출한다.
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
