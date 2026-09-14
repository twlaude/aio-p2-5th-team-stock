# Backend ↔ MCP Client 분석 계약

> **한눈에**
> 회원 요청에는 성향 네 값을 보냅니다.
> 온도·공시 근거는 규칙으로 계산합니다.
> Agent는 설명과 공시 추가 조회를 맡습니다.

## 연결

- 주소: `POST http://MCP_CLIENT_HOST:8010/internal/v1/common-analyses`
- 방식: HTTP REST + JSON
- 시간 제한: Backend 75초, MCP Client Workflow 60초
- 사용자 ID·로그인 토큰·아이디·비밀번호·대화 전체는 보내지 않습니다. 비회원은 `investment_profile: null`입니다.

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

Backend 검증 후 정식 기업명·6자리 코드를 받습니다. 성향은 Price·News·Disclosure·Community MCP에 보내지 않습니다. 자유 질문이 없어 `question`·`date_range`는 제외합니다.

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

`personalized_checkpoints`: `investment_profile`이 있을 때만 채웁니다. 비회원(`investment_profile: null`)은 생략 또는 `null`.
`price.volume_basis`·`price.volume_as_of`: Price MCP의 거래량 기준·거래일. 구버전 응답·일봉 실패는 생략 또는 `null`.

## 시장 관심 온도 v2

관심 온도 = 평소 대비 거래량·뉴스·커뮤니티 활동 + 공포탐욕 강도. 상승 가능성·매수 점수가 아닙니다. 입력을 0~1로 환산해 배점을 곱합니다.

| `components` key | 입력 | 정규화 | 배점 |
|---|---|---:|---:|
| `volume_activity` | `price.volume_ratio_20d`, 없으면 `1 + volume_change_rate / 100` | `clamp(ratio / 3, 0, 1)` | 30 |
| `news_attention` | `news.relevant_count`(없으면 `result_count`) + `news.span_hours` | 관련 기사 100건이 쌓이는 시간 `h = span_hours × 100 / count`. 6시간 이하 1, 168시간(7일) 이상 0, 사이는 로그 스케일. `span_hours` 없으면 `clamp(count / 80, 0, 1)` 폴백 | 25 |
| `community_activity` | `community.activity.ratio` | `clamp(ratio / 3, 0, 1)` | 25 |
| `fear_greed_intensity` | `community.fgi_latest.fgi` | `abs(fgi - 50) / 50` | 20 |

출처 `status` ≠ `success` 또는 입력 없음: 미가용으로 `components`에서 생략합니다.
`score` = `round(가용 항목 점수 합 / 가용 항목 배점 합 * 100)`, 가용 배점이 없으면 0입니다. `weight_covered`는 가용 배점 합(0~100)입니다. `data_coverage`·`label` 구간은 유지합니다.

## 공시 근거 v2

`evidence_level`: 자료 종류 수가 아닌 현재 이슈·최근 30일 주요 비정기 공시의 직접 연결입니다. 커뮤니티 중심, 제목에 정식 회사명이 있는 뉴스만 보조입니다. 임베딩(검색용 수치 변환)·유사도 점수는 쓰지 않습니다.

| 단계 | 판정 |
|---|---|
| `high` | 규칙 사전으로 현재 이슈와 연결된 주요 공시가 1건 이상 |
| `medium` | 연결 공시는 없지만 최근 30일 주요 공시가 1건 이상 |
| `low` | 최근 30일 주요 공시가 없음 |
| `low` (실패) | 주요 비정기 공시 조회 상태가 `success` 또는 `no_data`가 아님 |

- `evidence_level.matched[]`: `issue`·`report_name`·`receipt_number`·`published_at`. `unmatched[]`: 미연결 현재 이슈. `material_count`: 최근 30일 주요 공시 수.
- `sources[]`: 연결 이슈는 `confirmed`, 미연결 이슈는 첫 공시 source의 `unconfirmed`에 중복 없이 담습니다. `disclosure_kind`: `major`·`periodic`·`other`.
- 공시 source 순서(총 4건 이하): 연결 주요 공시 → 나머지 주요 공시 최대 1건 → 정기공시 최대 1건 → 사업보고서.

## MCP Client 책임

1. 네 MCP의 기본 Tool 6개(정기·주요 비정기 공시 포함)를 병렬 호출합니다. 외부 원본 API 직접 호출·원본 저장은 하지 않습니다.
2. LLM(언어 모델)에는 뉴스 최대 5건·관련 보고서 청크(조각) 3~5개·커뮤니티 집계만 보냅니다. 온도·근거는 확정 규칙으로 계산하고 LLM은 설명합니다.
3. Agent는 최대 3단계입니다. Tool 일부 실패 시 성공 자료를 유지해 `partial_success`로 반환합니다.
4. `investment_profile`이 있으면 공통 분석·성향 네 값으로 OpenAI `gpt-5.6-luna`가 `personalized_checkpoints`를 만듭니다. 이 값은 네 MCP에 보내지 않습니다.
5. 기본 조회는 AI가 고르지 않습니다. Luna Agent는 기본 조회 접수번호 중 최대 2건의 최근 공시 상세 Tool만 사용합니다.

진행 이벤트 payload(전달 데이터)에 판단·실행 주체 `owner`(`runtime`, `mcp`, `ai_agent`, `policy`)를 추가합니다.

## 종료 이유

성찰(오류 피드백 재호출)은 기존 필드 변경 없이 `trace_summary.reflections: int`를 추가합니다. 실제 추가 LLM 호출 수로 기본 0은 직렬화에서 생략(off 필드·값 유지)합니다. 여러 오류도 재호출 한 번이면 1입니다.
Runtime의 `AgentResult.reflections`에만 상세 오류를 남깁니다. 응답에 원문·Prompt는 금지합니다. `llm_calls`: on은 스키마 검증·Provider 실패 포함, off는 성공한 Provider 반환만 셉니다.
성찰 기본 2회는 기존 Agent 단계 상한 내에서 씁니다. 해소 오류는 `partial_failures` 제외, 기존 MCP 실패의 부분 성공은 유지합니다. `reflection_exhausted`: 성찰·단계 예산 부족 또는 스키마·서술 재검증 실패로 폴백(대체 응답) 종료.

```text
completed
no_data
partial_completed
model_error
invalid_tool_call
mcp_tool_error
max_steps_exceeded
workflow_timeout
reflection_exhausted
```
