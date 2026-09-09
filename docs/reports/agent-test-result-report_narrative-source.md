# 에이전트 시험 결과 보고서 — Backend `narrative_source` 분기

> MCP Client Agent(Luna)가 만든 서사를 신뢰할지, Backend가 대신 규칙 기반으로 조립할지 판단하는 `app/services/analysis/service.py`의 `_agent_narrative_ok()` 로직을 실제 API 호출로 검증한 기록.

## 1. 시험 목적

Backend가 다음 결정을 정확히 내리는지 확인합니다.

- **Scenario 1**: MCP Client Agent가 서사(narrative) 생성에 성공하면, Backend는 그 결과를 그대로 사용자에게 전달하는가?
- **Scenario 2**: Agent가 실패(`partial_failures`에 `service: "openai"` 존재)하면, Backend는 자체 규칙 기반 조립기(`compose_one_liner`, `compose_personal`)로 대체하는가?
- **Scenario 3**: 실제 live 환경에서도 이 경계가 그대로 작동하는가?

평가 흐름:

```text
Scenario 작성
→ POST /api/v1/analyses 실제 호출 (로컬 mock 모드 + live 모드)
→ 응답 JSON과 pytest 결과 수집
→ 기대 결과와 실제 결과 비교
→ PASS 또는 FAIL 기록
```

## 2. 시험 환경

| 항목 | 내용 |
| --- | --- |
| 시험 대상 | `backend/app/services/analysis/service.py`의 `run_analysis()`, `_agent_narrative_ok()` |
| 규칙 기반 조립기 | `backend/app/services/analysis/narrative.py`의 `compose_one_liner()`, `compose_personal()`, `pick_topic()` |
| 평가 코드 | `backend/tests/test_analysis.py`의 `test_agent_narrative_wins_when_agent_succeeded`, `test_backend_composes_when_agent_failed` |
| Tool 연결 | `POST /api/v1/analyses` (HTTP, Backend → MCP Client) |
| 로컬 환경 | `MCP_CLIENT_MODE=mock`, `NARRATIVE_SOURCE=agent_first`(기본값) |
| live 환경 | `159.223.75.71:8501` (Frontend 프록시 경유), `MCP_CLIENT_MODE=live` |
| 실행 일시 | 2026-09-07 |
| 실행자 | 윤기화 |

## 3. Scenario 1: Agent 서사 성공 → 그대로 사용

### 3.1 시험하려는 행동

`partial_failures`에 `service: "openai"` 항목이 없으면(=Agent가 서사 생성에 성공했다고 판단되면), Backend가 MCP Client의 `one_line_summary`·`personalized_checkpoints`를 가공 없이 그대로 사용자에게 전달하는지 확인합니다.

```python
SCENARIO = {
    "name": "Agent 서사 성공 시 그대로 전달",
    "input": {
        "query": "삼성전자",
        "user": "demo001 (로그인, 회원)",
        "mcp_client_mode": "mock",
    },
    "expected": {
        "one_line_summary_ends_with": "(Mock).",
        "personalized_checkpoints.personal_summary_starts_with": "장기 관점에서 보면",
    },
}
```

### 3.2 실행

```bash
cd infra && docker compose up -d
cd ../backend && python run.py &
python -m pytest -q tests/test_analysis.py -k agent_narrative
```

수동 재현(HTTP 직접 호출):
```python
r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"username": "demo001", "password": "Demo1234!"})
token = r.json()["access_token"]
r2 = httpx.post("http://localhost:8000/api/v1/analyses", json={"query": "삼성전자"}, headers={"Authorization": f"Bearer {token}"})
```

### 3.3 결과 기록

| 검사 항목 | 기대 결과 | 실제 결과 | 판정 |
| --- | --- | --- | --- |
| `one_line_summary` 접미사 | `(Mock).`로 끝남 | `"삼성전자의 최근 흐름을 뉴스·공시·커뮤니티 반응과 함께 정리했다(Mock)."` | PASS |
| `personalized_checkpoints.personal_summary` 접두사 | `"장기 관점에서 보면"`으로 시작 | `"장기 관점에서 보면: 삼성전자의 최근 흐름을..."` | PASS |
| pytest `test_agent_narrative_wins_when_agent_succeeded` | PASS | PASS | PASS |

최종 판정: **PASS**

### 3.4 Trace 증거 (실제 응답, 2026-09-07 로컬 실행)

```json
{
  "request_id": "32759ac7-68ad-4419-94d2-1a0ecb2c74b4",
  "status": "success",
  "access_level": "member",
  "one_line_summary": "삼성전자의 최근 흐름을 뉴스·공시·커뮤니티 반응과 함께 정리했다(Mock).",
  "detail": {
    "market_temperature": { "score": 52, "label": "보통", "data_coverage": ["price"], "weight_covered": 100 },
    "evidence_level": { "level": "low", "reason": "mcp_client 연결 전 Mock 데이터다.", "matched": [], "unmatched": [], "material_count": 0 },
    "news_summary": "mcp_client 연결 전 표본 뉴스 요약이다.",
    "disclosure_summary": "mcp_client 연결 전 표본 공시 요약이다.",
    "community_summary": "mcp_client 연결 전 표본 커뮤니티 요약이다."
  },
  "personalized_checkpoints": {
    "personal_summary": "장기 관점에서 보면: 삼성전자의 최근 흐름을 뉴스·공시·커뮤니티 반응과 함께 정리했다(Mock).",
    "priority_checks": [
      "선호 근거인 최근 뉴스부터 확인해보자.",
      "conservative 성향에 맞는 변동성 수준인지 점검해보자."
    ],
    "caution": "이 확인 포인트는 매수·매도를 추천하지 않으며 참고용 설명이다(Mock)."
  }
}
```

관찰 내용:

- `one_line_summary`가 mcp_client(Mock)의 원문 그대로 전달되었는가: **예**
- `personalized_checkpoints`가 규칙 기반 조립기(`compose_personal`)를 거치지 않고 원문 그대로 전달되었는가: **예** (`compose_personal` 특유의 "무리 없는 구간이에요" 같은 접두사가 없음)
- 실패 여부: 해당 없음(정상 통과)

## 4. Scenario 2: Agent 서사 실패 → Backend가 규칙 기반으로 조립

### 4.1 시험하려는 행동

`partial_failures`에 `{"service": "openai", "status": "model_error"}`가 있을 때, Backend가 `compose_one_liner()`/`compose_personal()`로 직접 문장을 조립해서 사용하는지 확인합니다. 이때도 원본 데이터(가격, 커뮤니티 토픽 등)는 그대로 유지되어야 합니다.

```python
SCENARIO = {
    "name": "Agent 실패 시 Backend 규칙 기반 조립",
    "input": {
        "query": "삼성전자",
        "user": "demo001 (로그인, 회원)",
        "mocked_partial_failures": [
            {"service": "openai", "status": "model_error", "message": "x"}
        ],
    },
    "expected": {
        "one_line_summary_starts_with": "뉴스는 HBM 메모리에 쏠려 있고",
        "personalized_checkpoints.personal_summary_starts_with": "무리 없는 구간이에요.",
    },
}
```

### 4.2 실행

```bash
python -m pytest -q tests/test_analysis.py -k backend_composes
```

`mcp_client.fetch_common_analysis`를 monkeypatch해서 `partial_failures`에 `openai: model_error`를 주입한 뒤 `run_analysis()`를 직접 호출(재현 스크립트는 6절 참고).

### 4.3 결과 기록

| 검사 항목 | 기대 결과 | 실제 결과 | 판정 |
| --- | --- | --- | --- |
| `one_line_summary` | 규칙 기반 문장(`compose_one_liner`) | `"뉴스는 HBM 메모리에 쏠려 있고, 공식 확인은 아직 조금이에요. 커뮤니티는 기대가 앞서요."` | PASS |
| `personalized_checkpoints.personal_summary` | 규칙 기반 문장(`compose_personal`), "무리 없는 구간이에요."로 시작 | `"무리 없는 구간이에요. 삼성전자는 관심과 확인된 재료가 비슷해요..."` | PASS |
| 원본 데이터(가격·소스) 유지 여부 | Mock 원본 그대로(current_price=70000 등) | 동일 | PASS |
| pytest `test_backend_composes_when_agent_failed` | PASS | PASS | PASS |

최종 판정: **PASS**

### 4.4 Trace 증거 (실제 응답, 2026-09-07 로컬 실행, `partial_failures` 인위 주입)

```json
{
  "request_id": "b971fd66-6026-4168-a5e4-53db711658a3",
  "status": "success",
  "access_level": "member",
  "one_line_summary": "뉴스는 HBM 메모리에 쏠려 있고, 공식 확인은 아직 조금이에요. 커뮤니티는 기대가 앞서요.",
  "personalized_checkpoints": {
    "personal_summary": "무리 없는 구간이에요. 삼성전자는 관심과 확인된 재료가 비슷해요. 손실을 피하는 걸 우선하는 오래 들고 가는 편인 당신은 HBM 메모리 실적 흐름만 꾸준히 보면 돼요.",
    "priority_checks": [
      "최근 기사 내용이 공시로 확인되는지",
      "HBM 메모리 관련 새 소식이 확인된 것인지",
      "배당·현금흐름이 유지되는지"
    ],
    "caution": "기대가 높을 땐 급하게 따라 사지 않아도 괜찮아요. 확인하고 들어가도 늦지 않아요."
  }
}
```

관찰 내용:

- 사용자에게 "AI가 실패했다"는 티가 전혀 안 나고 자연스러운 문장으로 대체되는가: **예**
- 가격(`current_price: 70000`)·소스 데이터는 Scenario 1과 동일하게 유지되는가(문장만 바뀌고 데이터는 안 바뀌는가): **예**
- 실패했다면 최초로 기대와 달라진 Event: 해당 없음

## 5. Scenario 3: live 환경에서 재현

### 5.1 배경

2026-09 초 live 환경 실황 페이지(`/api/v1/admin/live-status`)를 확인했을 때, 거의 모든 분석 요청에서 `partial_failures: [{"service": "openai", "status": "model_error"}]`가 관측되었다(별도 기록: 실황 페이지 스크린샷, 팀 내 공유). 즉 live 환경은 그 시점 기준 **거의 항상 Scenario 2 경로**를 타고 있었다.

### 5.2 실행

```python
r = httpx.post("http://159.223.75.71:8501/api/v1/auth/login", json={"username": "demo001", "password": "Demo1234!"})
token = r.json()["access_token"]
r2 = httpx.post("http://159.223.75.71:8501/api/v1/analyses", json={"query": "삼성전자"},
                headers={"Authorization": f"Bearer {token}"}, timeout=30.0)
```

### 5.3 결과 기록 (2026-09-07 재실행)

| 검사 항목 | 이전 관측(2026-09 초) | 이번 관측(2026-09-07) | 판정 |
| --- | --- | --- | --- |
| `one_line_summary` 성격 | 짧고 정형화된 규칙 기반 문장 | 매우 구체적인 서술형 문장(뉴스 다건 종합, 공시 2건 교차 확인) | 변화 감지 |
| `personalized_checkpoints` 성격 | 규칙 기반 템플릿(고정 문구 조합) | 사업보고서 수치(`DS 부문 매출 130조1,282억원, 영업이익 24조8,581억원`)까지 인용하는 상세 서술 | 변화 감지 |
| `partial_failures`(openai) 직접 확인 | 실황 페이지에서 직접 확인함 | **확인 못 함** — live 환경 관리자 비밀번호가 배포 시 변경되어 `/api/v1/admin/live-status` 접근 실패(401) | 미확인(제약) |

최종 판정: **조건부 PASS** — 사용자 응답의 내용 품질로 미루어 Agent(OpenAI) 호출이 이번엔 성공한 것으로 보이나, `partial_failures` 필드를 직접 조회하지 못해 100% 확정은 아님.

### 5.4 Trace 증거 (live 환경 실제 응답, 2026-09-07, 일부 발췌)

```json
{
  "request_id": "a3e8f190-412d-4ea4-9500-01c51aab40ec",
  "one_line_summary": "뉴스는 성과급 갈등과 메모리 기대에 쏠려 있고, 주요 공시는 있지만 지금 화제와는 달라요. 커뮤니티는 기대와 우려가 엇갈려요.",
  "detail": {
    "evidence_level": {
      "level": "medium",
      "reason": "최근 30일 주요 공시 1건은 있지만 지금 화제(해외 메모리주 강세의 동반 수혜)와 직접 연결되진 않아요",
      "unmatched": [
        "해외 메모리주 강세의 동반 수혜",
        "오픈AI 관련 상승 동력",
        "메모리 공급 부족에 따른 업황 반전",
        "27만원 부근 매도벽",
        "개인 매물 출회",
        "성과급에 뿔난 주주단체…삼성전자 이사회·노조 추가 고발"
      ],
      "material_count": 1
    }
  },
  "personalized_checkpoints": {
    "personal_summary": "평소 기준대로 보면 돼요.\n당신은 손실을 피하는 걸 우선하는 오래 들고 가는 편이고, 이 종목은 관심 온도 41점에 근거 수준도 medium이라 기대와 확인 정도가 비슷해요. 먼저 재무 흐름과 공시를 확인한 뒤, 장기 보유에 필요한 현금흐름을 살펴보는 순서가 맞아요.",
    "priority_checks": [
      "최근 사업보고서의 매출·영업이익 흐름을 확인하세요. 2025년 사업보고서에는 DS 부문 매출 130조1,282억원, 영업이익 24조8,581억원이 기재돼 있지만, 전체 최근 추세는 반기보고서와 함께 다시 확인해야 해요.",
      "해외 메모리주 강세와 메모리 공급 부족에 따른 업황 반전이 공시로 확인되는지 살펴보세요. 현재는 관련 화제와 직접 연결되는 matched 공시가 없어요.",
      "배당·현금흐름이 유지되는지 확인하세요. 사업보고서는 유동성 관리를 설명하지만, 제공된 자료만으로 향후 유지 여부까지 판단할 수는 없어요."
    ]
  }
}
```

관찰 내용:

- Scenario 2의 규칙 기반 문장(고정 어투: "~에 쏠려 있고", "무리 없는 구간이에요")과 이번 응답을 비교하면, 이번 응답은 `unmatched` 이슈 목록·구체적 재무 수치 인용 등 **규칙 기반 조립기가 만들 수 없는 내용**을 포함한다.
- 이는 이번 요청에서는 `_agent_narrative_ok()`가 `True`(Agent 성공)로 판정되어 Scenario 1 경로로 처리됐다고 볼 수 있다.
- 다만 `partial_failures`를 직접 조회하지 못했으므로, "이전엔 항상 실패했는데 지금은 항상 성공한다"는 결론은 **아직 확정할 수 없다** — 표본 1건으로 판단한 정황 증거일 뿐이다.

## 6. Scenario 2 재현 스크립트 (참고용)

```python
import asyncio
from app.clients.mcp_client import client as mcp_client_module
from app.services.analysis.service import run_analysis
from app.schemas.user import CurrentUser
import app.services.analysis.service as svc

original = mcp_client_module.fetch_common_analysis

async def failed_agent(*args, **kwargs):
    raw = await original(*args, **kwargs)
    raw["partial_failures"] = [{
        "service": "openai", "status": "model_error",
        "message": "Luna 분석을 완료하지 못해 규칙 기반 설명을 제공합니다.",
        "retryable": True,
    }]
    return raw

svc.mcp_client.fetch_common_analysis = failed_agent

async def main():
    user = CurrentUser(user_id="demo-001", username="demo001", display_name="데모 사용자 1")
    result = await run_analysis("삼성전자", user)
    print(result.model_dump())

asyncio.run(main())
```

## 7. 시험 결과 요약

| Scenario | 핵심 평가 기준 | 결과 |
| --- | --- | --- |
| Scenario 1: Agent 서사 성공 | 성공 시 원문 그대로 전달 | PASS |
| Scenario 2: Agent 서사 실패 | 실패 시 규칙 기반 조립, 데이터는 유지 | PASS |
| Scenario 3: live 환경 재현 | live 환경에서도 같은 경계 작동 | 조건부 PASS(관측 제약 있음) |

전체 결과: **PASS** (단, Scenario 3은 `partial_failures` 직접 확인 없이 응답 품질로 추정한 정황 증거 기반)

## 8. 발견한 문제와 개선

### 발견한 문제

1. Backend의 `agent_first`/`backend` 안전망 자체는 의도대로 정확히 작동한다 — 이 부분은 문제 없음.
2. **live 환경의 OpenAI 연동 안정성은 여전히 불확실하다.** 2026-09 초에는 거의 매 요청마다 `openai: model_error`가 관측되었는데, 이번(2026-09-07) 표본 1건은 성공한 것으로 보인다. 실패율이 얼마나 되는지, 개선이 실제로 있었는지는 `partial_failures`를 다건 표본으로 다시 확인해야 한다.
3. live 환경 관리자 페이지(`/api/v1/admin/live-status`) 접근 정보가 팀 내에서 공유되지 않아, 이번 시험에서 Scenario 3의 `partial_failures`를 직접 확인하지 못했다.

### 원인

- 1, 2는 Backend 코드 문제가 아니라 **mcp_client의 Agent/OpenAI 연동** 영역 문제로 추정된다(권오현님 담당 영역).
- 3은 절차 문제(관리자 인증정보 공유 누락)다.

### 수정 내용

- 이번 시험에서는 코드 수정 없음(관측 및 검증 목적).

### 재시험 결과

| 항목 | 수정 전 | 수정 후 |
| --- | --- | --- |
| 실패한 검사 | 없음 | - |
| 최초 실패 Event | 없음 | - |
| 최종 판정 | PASS | - |

## 9. 결론

Backend의 `narrative_source` 안전망(`agent_first` → 실패 시 `backend` 규칙 기반 조립)은 로컬 mock 환경에서 두 경로 모두 pytest와 실제 HTTP 호출로 검증했고, 두 경우 모두 PASS했다. live 환경에서도 최소 1건은 Agent 성공 경로가 정상 작동함을 확인했다.

- 확인된 정상 행동: Agent 성공/실패 여부와 무관하게 사용자에게는 항상 자연스러운 문장이 나가고, 원본 데이터(가격·근거)는 두 경로에서 동일하게 보존된다.
- 남아 있는 문제: live 환경의 OpenAI 연동이 실제로 얼마나 자주 실패하는지 다건 표본으로 재확인 필요. 관리자 페이지 접근 정보 팀 공유 필요.
- 다음에 추가할 Scenario: live 환경에서 `partial_failures`를 여러 건(예: 10건) 연속 수집해 실패율 정량화 / `NARRATIVE_SOURCE=backend` 강제 설정 시 항상 규칙 기반으로만 가는지(이미 pytest에 `test_guest_one_liner_uses_frontend_rule`, `test_member_personal_summary_uses_risk_gap_rule`로 커버됨, 표에 추가 반영 검토) / mcp_client 자체가 완전히 응답 불가할 때(`MCPClientUnavailable`)의 사용자 노출 메시지 검증.

대표 Scenario가 통과했다는 사실만으로 live 환경의 OpenAI 연동이 완전히 안정적이라고 결론 내리지 않는다. 실패율 재측정 결과가 나오면 이 문서에 이어서 기록한다.
