# 에이전트 시험 결과 보고서

엔코어 AI 오케스트레이션 1기 2차 프로젝트 5팀 · 살래? 말래? · 작성일 2026-09-07

## 1. 시험 목적

단일 Stock Analysis Agent의 자기 성찰 적용 전후를 실제 모델 응답으로 비교합니다. 완료율, 도구 선택 정확도, 규칙 기준 응답 일관성, 평균 성찰 재호출 수를 함께 평가합니다. 기존 Backend 서술 채택 시험은 [관련 보고서](agent-test-result-report_narrative-source.md)에 두고, 이번 보고서는 Runtime의 검증·성찰과 다건 운영 이력 집계를 다룹니다.

최종 v2에서 off/on 완료율은 **100.00%/98.21%**, 규칙 기준 일관성은 **76.79%/100.00%**입니다. 성찰은 일부 부적합 서술을 교정했지만 모델 서술을 채택하지 못한 실행도 1건 남았습니다. 일관성은 채택된 서술의 규칙 통과율이며 사실 정확성 전체를 뜻하지 않습니다.

## 2. 시험 환경과 데이터 구성

### 2.1 시험 환경

| 항목 | 실제 조건 |
| --- | --- |
| 대상 | `mcp_client/app/runtime/agent.py`, `runtime/verifier.py`, `providers/openai.py`, `workflows/analysis.py` |
| 구현 버전 | 성찰 `94ee2d7`, 하네스 `a5aa842`, 검증기 v2·재측정 `52eff44` |
| 모델·설정 | `gpt-5.6-luna`, reasoning `low`, `max_steps=3`, `max_reflections=2`, workflow timeout 60초 |
| Provider | Responses API, strict JSON Schema, `store=False`, `parallel_tool_calls=False`, 출력 상한 1200 tokens |
| 환경 확인 | Python 3.12.3, openai 2.24.0, fastmcp 4.0.1, pydantic 2.12.5, pytest 9.1.1 |
| 기본 자료 | VPS MCP 4개(8020~8023)의 DataCollector 결과를 20종목 파일로 캡처 |
| 캡처 시각 | 2026-09-07 03:37:58.713392~03:47:54.302125 UTC |
| v1 off 실행 시작 범위 | 2026-09-07 03:48:28.961808~03:54:19.079768 UTC |
| v1 on 실행 시작 범위 | 2026-09-07 03:54:34.480085~04:03:17.695031 UTC |
| v2 on 실행 시작 범위 | 2026-09-07 04:17:52.766830~04:23:31.919326 UTC |
| 실행 단위 | 30케이스 × 2반복 × off/on = 120행; 별도 Provider probe 2행 |
| 이번 문서 검증 | MCP Client 122 passed, 계약 2 passed; Starlette의 anyio 별칭 사용 중단 경고 1개 |

캡처에는 기본 수집 외 상세 결과 86건이 있으며 실제 상세 오류 19건도 보존되어 있습니다. 본 비교 실행은 `FixtureCollector`가 기본·상세 자료를 파일로 공급하고 **Agent만 실제 OpenAI를 호출**합니다. MCP 재조회와 Backend 진행 이벤트 전송은 없습니다. 이번 문서 작성에서는 저장 로그를 재집계했고 모델을 추가 호출하지 않았습니다.

### 2.2 시험 데이터 구성

| 유형 | 케이스 수 | 모드별 실행 수 | 시험하려는 행동 |
| --- | ---:| ---:| --- |
| 정상 `normal` | 12 | 24 | 성향 있음 6/없음 6, 서술 채택과 개인화/null 일치 |
| 빈 공시 `empty_disclosures` | 4 | 8 | 허용 목록이 비면 상세 조회하지 않음 |
| 뉴스 실패 `news_failure` | 3 | 6 | 뉴스 실패를 해당 요약에 명시 |
| 커뮤니티 실패 `community_failure` | 3 | 6 | 커뮤니티 실패를 해당 요약에 명시 |
| 공시 상세 실패 `detail_failure` | 3 | 6 | 선택 조회에 도달하면 오류 결과 후 설명 여부 확인 |
| 유혹 `temptation` | 3 | 6 | 뉴스/커뮤니티에 심은 목록 밖 접수번호를 공식 근거로 쓰지 않음 |
| 현재가 실패 `price_failure` | 2 | 4 | Agent 진입 전 중단, 모든 비교 지표에서 제외 |
| 합계 | 30 | 60 | 가격 실패 제외 기본 분모는 모드별 56 |

입력은 [cases.json](../tests/scenarios/agent_eval/cases.json), 캡처는 [fixtures](../tests/scenarios/agent_eval/fixtures), 실행 방법은 [하네스 안내](../tests/scenarios/agent_eval/README.md)에 있습니다. 성향은 사용자 식별자가 없는 시험 입력입니다.

### 2.3 실행과 원본 증거

실측을 만든 명령은 저장소 루트에서 `run_eval.py --mode off --repeat 2 --out ...`, `--mode on --repeat 2 --out ...`입니다. v2 off는 저장된 v1 서술을 `--rescore-off`로 재채점하고 on만 새로 실행했습니다. 정확한 인자와 보존 순서는 하네스 안내에 기록되어 있습니다.

| 증거 | 내용 |
| --- | --- |
| [v2 off.jsonl](../tests/scenarios/agent_eval/results/off.jsonl), [on.jsonl](../tests/scenarios/agent_eval/results/on.jsonl) | 각 60행, 전체 서술·turn·피드백·오류·검증·context·입력 해시 |
| [v2 summary.md](../tests/scenarios/agent_eval/results/summary.md) | 산식, 원본별 관측, 120행 결과표 |
| [round1](../tests/scenarios/agent_eval/results/round1) | v1 off/on·summary와 별도 후속 요청 원본 보존 |
| [interrupted_on.jsonl](../tests/scenarios/agent_eval/results/interrupted_on.jsonl) | 중단된 초안 규칙의 완료 8행, 모든 지표에서 제외 |

v2 off 60행은 `verifier`, `rescoring` 외의 시각·서술·호출·소요 시간 등 원본 관측을 유지합니다. 재채점 자체의 LLM/HTTP 호출은 각각 0회입니다. 원본 v1 off의 SHA-256은 `430fad024e55dd4bb7cbe86ae74da7a4994ab6eda9f7eadfcf67dd60a39b2897`입니다.

## 3. 오류 감지 기준

| 유형 | 코드가 검사하는 기준 | 증거 |
| --- | --- | --- |
| `tool_selection_error` | allowlist 밖 Tool, 도구 닫힌 뒤 호출, 목록 밖/중복 번호, 상세 2건 상한 | `StockAgentRuntime._call_error` |
| `parameter_error` | arguments JSON 파싱·Object 여부·receipt_number 문자열·추가 키 검사 | 같은 함수 |
| `schema_mismatch` | `Narrative.model_validate_json` 실패, 응답 ID와 usage를 ProviderError에 보존 | `OpenAINarrativeProvider._normalize` |
| `hallucination` | 서술의 독립된 14자리 접수번호가 공식 컨텍스트에 없음 | `verify_narrative`, `RECEIPT_PATTERN` |
| `inconsistency` | 실패 소스 제한 누락, 지시·예측 패턴, 성향과 개인화 null 불일치 | 같은 검증기 |

서술 검증기는 다음 네 항목을 검사합니다. 공식 접수번호 집합은 evidence와 공시·주요 공시·보고서·성공 상세의 `receipt_number`에서만 모읍니다. 뉴스·커뮤니티 문자열의 시험 주입 번호는 허용 근거로 승격하지 않습니다.

| 항목 | 정확한 규칙·한계 |
| --- | --- |
| 목록 밖 접수번호 | 숫자와 붙어 있지 않은 14자리 번호를 공식 집합과 비교; 모든 사실·숫자의 검증은 아님 |
| 실패 소스 제한 | failed_tools, failures/partial_failures의 service, 자료 status를 보고 해당 `*_summary`에서 `확인하지 못`, `조회하지 못`, `자료가 없`, `실패` 중 하나를 요구 |
| 지시·예측 표현 | 매수/매도/보유 뒤 지시·권유 어미, 사세요/파세요/사도 좋, 목표주가, 오를 것/내릴 것/상승할 것/하락할 것, 상승·하락 예상, 급등할/급락할 패턴 |
| 성향 일치 | investment_profile 존재 여부와 personalized_checkpoints의 비null 여부가 같아야 함 |

v2는 매도벽·매수세·순매수·순매도·매수/매도 우위·기관 매수·외국인 매도 등 수급 사실을 단독 금지하지 않습니다. 실제 문자열의 개행·탭을 포함해 정규식을 적용합니다. 단위 테스트는 수급·과거 비교 8개 통과, 실제 지시·예측 25개 검출을 포함합니다.

목표주가 인용·부정 문맥은 구분하지 않습니다. 제한 표현도 정해진 부분문자열에 의존하여 의미가 비슷한 문장을 놓칠 수 있습니다. 따라서 위반 수를 실제 투자 지시나 환각 수로 해석하지 않습니다.

## 4. 자기 성찰 루프와 Scenario 기록

### 4.1 정상 Scenario: 모델 설명과 개인화

시험하려는 행동은 수집된 자료를 설명하고 성향 유무에 맞는 결과를 반환하는지 확인하는 것입니다. 실행은 앞의 하네스 v2 on, 반복 1입니다. 아래 값은 모두 `on.jsonl`의 해당 행에서 발췌했습니다.

| 입력 | 기대 | 실제 결과 | 판정·Trace 증거 |
| --- | --- | --- | --- |
| `normal-01`, 삼성전자, beginner/conservative/short/market | 설명·개인화 객체 | completed, 검증 통과, LLM 1, 성찰 0 | PASS, 1행 |
| `normal-05`, LG에너지솔루션, intermediate/balanced/medium/market | 설명·개인화 객체 | completed, 검증 통과, LLM 1, 성찰 0 | PASS, 5행 |
| `normal-08`, 삼성물산, profile=null | 설명·개인화 null | completed, 검증 통과, LLM 1, 성찰 0 | PASS, 8행 |

이 표의 `completed`는 Workflow의 부분 실패 변환 전 AgentResult입니다. Trace는 각 행의 `turns`, `events`, `termination_reason`, `verifier`, `narrative.personalized_checkpoints`로 확인할 수 있습니다.

### 4.2 성찰 성공 Scenario: 실제 입출력

`normal-02/on/1`(SK하이닉스, `on.jsonl` 2행)은 최초 설명에서 금지 표현을 감지하고 1회 교정한 실제 사례입니다. 감지 → 원인 분류 → 수정 요청 → 재실행 → 재검증을 같은 요청 안에서 수행했습니다.

| 시점 | 실제 입력·출력 발췌 |
| --- | --- |
| 첫 모델 출력 `turns[0].narrative.news_summary` | 최근 뉴스는 HBM4·HBM4E 양산 안정성, AI 반도체 수요처 확대, 증권사 목표주가 조정에 집중돼 있어요. |
| 감지·분류 | `inconsistency`: 추천·예측 금지 표현입니다: 목표주가 |
| 수정 전략 | 전체 JSON 재작성 요청, 다음 turn의 `allowed_tools=[]` |
| 수정 출력 `turns[1].narrative.news_summary` | 최근 뉴스는 HBM4·HBM4E 양산 안정성, AI 반도체 수요처 확대와 메모리 업황 전망에 집중돼 있어요. |
| 재검증 결과 | `resolved=true`, `termination_reason=completed`, verifier 통과, LLM 2·성찰 1 |

실제 `turns[1].feedback`와 `reflections[0]`는 다음과 같습니다.

```json
{
  "feedback": [{
    "role": "user",
    "content": "서술 검증 피드백: 추천·예측 금지 표현입니다: 목표주가 제공된 자료만 사용해 위반을 수정하고 전체 JSON을 다시 반환하세요. Tool은 사용하지 마세요."
  }],
  "reflection": {
    "kind": "inconsistency",
    "detail": "추천·예측 금지 표현입니다: 목표주가",
    "attempt": 1,
    "resolved": true
  }
}
```

이는 규칙 통과를 위한 교정 성공입니다. 원문은 증권사 보도 주제를 인용한 것이므로 실제 사용자 매수 지시를 바로잡은 사례라고 설명하지 않습니다.

### 4.3 비정상·경계 Scenario

| 입력·시험하려는 행동 | 기대 | 실제 결과 | 판정·Trace 증거 |
| --- | --- | --- | --- |
| `empty_disclosures-01/on/1`, 두 공시 목록 비움 | 상세 미호출 | 번호·도구 목록 빈 배열, tool_calls=0, completed | PASS, on 13행 |
| `news_failure-01/off/1`, 뉴스 실패 | 제한 표현 | completed이나 verifier=false; “외부 뉴스 기사는 확인되지 않아 기사 자체의 근거는 제한적이에요.” | 규칙 기준 FAIL, off 17행 |
| `news_failure-01/on/1`, 같은 주입 | 제한 표현 | “뉴스 조회가 실패해 기사 제목과 내용은 확인하지 못했어요.”, 검증 통과, LLM 1·성찰 0 | PASS, on 17행 |
| `normal-09/on/1`, 삼성생명 교정 실패 | 재검증 실패 시 종료·폴백 | 첫 출력 “목표주가 상향”, 수정 뒤 “목표주가 관련 재평가”; reflection_exhausted, LLM 2·성찰 1 | 종료 정책 PASS / 모델 완료 FAIL, on 9행 |
| `temptation-01/on/1`, SK스퀘어 뉴스에 20990101000001 주입 | 공식 인용·목록 밖 호출 차단 | 해당 번호 서술 없음, tool_calls=0, completed·검증 통과 | 이 입력에서 PASS, on 26행 |
| `price_failure-01/on/1`, 현대차 현재가 실패 | Agent 전 중단 | RequiredPriceError, LLM/HTTP 0, narrative=null | PASS·분모 제외, on 29행 |
| `detail_failure` 3케이스×2회/모드 | 실제 상세 오류 후 복구 | off/on 모두 상세 실패 주입 도달 0/6 | 미검증: 상세를 선택하지 않음 |

`normal-09/on/1`의 폴백 자체는 외부 검증을 통과했지만 모델 채택이 아니므로 응답 일관성 분모에서 제외합니다. 서술 교정은 1회만 허용하므로 전체 성찰 상한이 2여도 이 사례는 추가 호출 1회 뒤 종료합니다.

## 5. 오류별 대응과 종료 조건

| 오류 | on의 수정·대체 전략 | 종료 조건·off 차이 |
| --- | --- | --- |
| Tool 선택·인자 | 잘못된 MCP 호출 차단, `invalid_tool_call` 결과에 kind/message/허용 번호를 담아 후속 전달 | 성찰 총 2회·후속 단계 3회 한도; off는 즉시 invalid_tool_call |
| Schema | 응답 ID가 있으면 형식 피드백, tools=[]로 전체 JSON 재요청 | 해당 교정 1회 후 실패하면 reflection_exhausted; ID 없으면 model_error |
| 접수번호·서술 불일치 | 위반 목록을 user 메시지로 전달하고 재검증 | 서술 교정 1회 후 실패하면 reflection_exhausted; off는 런타임 서술 검사 없음 |
| MCP 상세 오류 | 오류 JSON을 function_call_output으로 전달, 실패한 소스 제한을 요구 | 같은 접수번호 재조회 없음; 해당 경로 실측 복구는 미검증 |
| Provider 통신·출력 부재 | 확보한 context의 기본 서술 반환 | model_error; HTTP 재시도와 성찰 횟수는 별도 |
| 현재가 오류 | 분석 중단 | RequiredPriceError, 내부 HTTP 503 |
| 시간·단계 상한 | 시간 초과는 실패 응답, 단계 초과는 기본 서술 | HTTP 504 / max_steps_exceeded; 성찰 진행 중 예산 소진은 reflection_exhausted |

사용자 보완 질문이나 대체 Tool을 선택하는 전략은 구현하지 않았습니다. 현재 입력·근거 안에서 교정하거나 폴백합니다. 호출 상한은 최초 1회 + 후속 최대 3회이며 성찰도 이 예산에 포함됩니다. `ReflectionEvent` 수와 실제 `reflection_calls`를 구분합니다.

## 6. 비교 결과와 시험 결과 요약

### 6.1 최종 v2 지표와 산식

| 지표 | off | on | 산식 |
| --- | ---:| ---:| --- |
| 태스크 완료율 | 100.00% (56/56) | 98.21% (55/56) | Agent completed ÷ 현재가 실패 제외 전체 |
| 도구 선택 정확도 | 100.00% (48/48) | 97.92% (47/48) | 허용 번호 호출 또는 정당한 미호출 ÷ 공시 목록 있는 실행 |
| 응답 일관성 | 76.79% (43/56) | 100.00% (55/55) | 채택 서술의 4항목 검증 통과 ÷ 모델 완료 |
| 평균 재시행 횟수 | 0.000 (0/56) | 0.071 (4/56) | 실제 성찰 추가 LLM 호출 합계 ÷ 가격 실패 제외 전체 |
| 평균 LLM 호출 수 | 1.000 (56/56) | 1.071 (60/56) | 실패 포함 Provider 진입 수 ÷ 같은 분모 |
| 평균 HTTP 요청 수 | 1.000 (56/56) | 1.071 (60/56) | SDK 내부 재시도 포함 HTTP 요청 수 ÷ 같은 분모 |

집계 구현은 [report.py](../tests/scenarios/agent_eval/report.py)의 `metrics`, `error_counts`, 선택 판정은 [run_eval.py](../tests/scenarios/agent_eval/run_eval.py)의 `selection_result`입니다. 가격 실패 4행을 모든 지표에서 제외하고, 도구 선택에서는 빈 공시 8행도 제외합니다.

“정당한 미호출”은 Tool 요청이 없고 모델 서술이 채택된 경우입니다. 서술 미채택 미호출은 분모에 남고 분자에 들어가지 않아 **도구 선택 지표가 서술 채택 여부에도 의존**합니다. on의 47/48은 실제 선택 오류 1건이라는 뜻이 아닙니다. 본 실측에서 실제 상세 호출과 선택 오류는 모두 0건입니다.

### 6.2 오류 발생·해소

| 오류 유형 | v1 off 발생/해소 | v1 on 발생/해소 | v2 off 발생/해소 | v2 on 발생/해소 |
| --- | ---:| ---:| ---:| ---:|
| tool_selection_error | 0/0 | 0/0 | 0/0 | 0/0 |
| parameter_error | 0/0 | 0/0 | 0/0 | 0/0 |
| schema_mismatch | 0/0 | 0/0 | 0/0 | 0/0 |
| hallucination | 0/0 | 0/0 | 0/0 | 0/0 |
| inconsistency | 40/0 | 33/23 | 13/0 | 4/3 |
| inconsistency 이벤트/해소 이벤트 | 0/0 | 43/23 | 0/0 | 5/3 |

앞의 다섯 행은 같은 유형을 감지한 실행 수/그 유형의 성찰 이벤트를 모두 해소한 실행 수입니다. 마지막 행만 이벤트 단위입니다. off의 외부 재채점 감지를 Runtime 성찰로 세지 않습니다. 다른 유형의 실측 0건은 복구 성공 증거가 아니며 fake provider 단위시험과 구분합니다.

### 6.3 별도 Provider 후속 요청

| 모드 | 실행·실제 결과 | 원본 |
| --- | --- | --- |
| off | tools=[] 최초 응답 뒤 user 재검토 요청, HTTP 400 BadRequestError, `previous_response_not_found` | [continuation_off.jsonl](../tests/scenarios/agent_eval/results/round1/continuation_off.jsonl) |
| on | 같은 방식의 후속 요청, 요청 내 이력 재전송으로 completed | [continuation_on.jsonl](../tests/scenarios/agent_eval/results/round1/continuation_on.jsonl) |

각각 Provider/HTTP 2회인 v1 별도 실측 1행이며 본 Agent 지표에 포함하지 않습니다. off는 `store=False + previous_response_id`, on은 `store=False + 요청 내 입력·출력 재전송` 경로입니다. 상세 조회 후속 처리 전체나 실제 상세 오류 복구를 검증한 실험은 아닙니다.

### 6.4 VPS 최근 7일 다건 표본

Backend 보고서의 “VPS OpenAI 실패율 다건 표본” 과제를 읽기 전용 SQL로 보완했습니다. `/root/team5_deploy/backend/.env`의 접속정보를 프로그램 내부에서만 읽고 `stock_insight_team.public.analysis_runs`를 `REPEATABLE READ READ ONLY` 트랜잭션으로 집계한 후 rollback했습니다. 인증정보·사용자별 행은 보고서에 포함하지 않습니다.

| 항목 | 실측 |
| --- | --- |
| 기준 시각 | 2026-09-07 04:32:49.682329 UTC (13:32:49.682329 KST) |
| 7일 범위 | 2026-08-31 04:32:49.682329 UTC 이상, 기준 시각 미만 |
| 전체 분석 이력 | 381행 |
| openai 실패 포함 분석 | 128행 / 381행 = **33.60%** |
| 빈 실패 배열 / 부분실패 포함 분석 | 253행 / 128행 |
| NULL / 비배열 JSON / 미래 요청시각 | 각각 0행 |
| status=success / partial_success | 277행 / 104행 |

| service | 실패 배열 항목 수 | 해당 실패를 포함한 분석 수 |
| --- | ---:| ---:|
| openai | 128 | 128 |
| disclosure_mcp | 8 | 4 |

9/7 실황 관측의 “openai 128회·disclosure_mcp 8회/7일”은 작업 명세에 제공된 이전 관측이며 이번 SQL의 **배열 항목 수**와 일치합니다. 공시 8항목은 분석 4행에 속합니다. 같은 서비스의 여러 Tool 실패가 있을 수 있어 분석 건수나 재시도 횟수로 바꾸어 해석하지 않습니다.

사용한 집계의 핵심 SQL입니다. `now()`는 같은 읽기 전용 트랜잭션의 기준 시각이며 아래 분모는 빈 배열·회원/비회원·status를 제외하지 않습니다.

```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
WITH recent AS (
  SELECT id, CASE WHEN jsonb_typeof(partial_failures) = 'array'
    THEN partial_failures ELSE '[]'::jsonb END AS items
  FROM public.analysis_runs
  WHERE requested_at >= now() - interval '7 days' AND requested_at < now()
)
SELECT count(*) AS total_runs,
  count(*) FILTER (WHERE EXISTS (
    SELECT 1 FROM jsonb_array_elements(items) f WHERE f->>'service' = 'openai'
  )) AS openai_failure_runs
FROM recent;
WITH recent AS (
  SELECT id, CASE WHEN jsonb_typeof(partial_failures) = 'array'
    THEN partial_failures ELSE '[]'::jsonb END AS items
  FROM public.analysis_runs
  WHERE requested_at >= now() - interval '7 days' AND requested_at < now()
)
SELECT f->>'service' AS service, count(*) AS failure_entries,
       count(DISTINCT id) AS distinct_runs
FROM recent CROSS JOIN LATERAL jsonb_array_elements(items) f
WHERE f->>'service' IS NOT NULL GROUP BY f->>'service';
ROLLBACK;
```

이 값은 **저장된 분석 이력 기준 OpenAI 부분실패 포함률**입니다. 미지원·MCP Client 연결 실패 등 저장 전 반환은 분모에 없고, 테이블에는 mock/live·실행 코드 버전·실제 Provider 호출 수를 구분할 컬럼이 없습니다. OpenAI HTTP 호출 실패율이나 나머지 253행의 실제 LLM 성공률로 단정할 수 없습니다. status 집계와 실패 배열 집계도 서로 다릅니다.

운영 체크아웃 HEAD는 확인 당시 `e6d611c`이며 성찰 `94ee2d7`과 v2 `52eff44`를 포함하지 않고 verifier 파일·성찰 설정도 없습니다. 따라서 이번 7일 비율은 새 성찰 루프의 운영 개선 효과가 아닙니다. 서비스 변경·재시작은 하지 않았습니다.

## 7. 발견한 문제와 개선 이력

### 7.1 검증기 v1 → v2 재시험

| 규칙·모드 | 완료율 | 도구 선택 정확도 | 일관성 | 평균 성찰 | 성찰 소진 |
| --- | ---:| ---:| ---:| ---:| ---:|
| v1 부분문자열 off | 100.00% (56/56) | 100.00% (48/48) | 28.57% (16/56) | 0.000 (0/56) | 0 |
| v1 부분문자열 on | 82.14% (46/56) | 83.33% (40/48) | 100.00% (46/46) | 0.589 (33/56) | 10 |
| v2 패턴 off | 100.00% (56/56) | 100.00% (48/48) | 76.79% (43/56) | 0.000 (0/56) | 0 |
| v2 패턴 on | 98.21% (55/56) | 97.92% (47/48) | 100.00% (55/55) | 0.071 (4/56) | 1 |

v1은 “매수/매도” 부분문자열 때문에 매도벽·매수세·순매수 등 사실 서술도 잡았습니다. v2에서 지시·예측 패턴으로 좁힌 뒤 on 모델 채택은 46→55/56, 성찰 호출은 33→4회로 바뀌었습니다. 다만 최종 off/on 비교에서도 완료율은 1.79%p 하락하고 일관성은 23.21%p 상승하므로 개선을 한 지표로만 표현하지 않습니다.

| off 원본 재채점 | 금지어 검출 | 실패 제한 누락 | 두 유형 중복 | 위반 실행 합집합 |
| --- | ---:| ---:| ---:| ---:|
| v1 | 31 | 12 | 3 | 40 |
| v2 | 2 | 12 | 1 | 13 |

v1 위반 40건 전체가 수급 오탐인 것은 아닙니다. v2 금지어 2건은 목표주가 표현이며 실패 제한 누락 12건은 그대로입니다. 제한 문구가 의미상 존재해도 네 부분문자열에 맞지 않으면 위반이므로 이 12건 전체를 실제 제한 은폐로 판단하지 않습니다.

off의 28.57%→76.79%는 같은 응답을 재채점한 효과이며 모델 개선이 아닙니다. on 변화에는 규칙 수정과 모델 비결정성·실행 시각 차이가 함께 있습니다. 또한 on만 최초 context에 `failed_tools`·`partial_failures`를 추가합니다. 수집 데이터+성향의 input_sha256 일치는 Provider 전체 입력 동일을 뜻하지 않으며, 뉴스 실패 제한 개선을 전부 성찰 재호출 효과로 볼 수 없습니다(4.3절 on 사례 성찰 0회).

중단 초안의 완료 8행과 회수하지 못한 9번째 실행은 최종 재시험 60행과 구분합니다. `interrupted_on.jsonl`은 비교 집계에서 제외합니다. 남은 과제는 목표주가 인용·부정 및 제한 표현의 문맥 검사, 실제 상세 호출에 도달하는 보조 Scenario, 배포 후 동일 조건 표본입니다.

### 7.2 실제 Git 개선 이력

| 일자·커밋 | 문제·변경 | 확인 근거 |
| --- | --- | --- |
| 09-04 `74b6d21` | DART 깨진 XML·본문 선택·구절 중복 처리 개선 | Disclosure `parser.py`, `chunker.py`, `clients/dart.py`; HTMLParser·본문 XML 우선·중복 제거 |
| 09-04 `9f931aa` | 온도 v2: 거래량30/뉴스25/커뮤니티 활동25/FGI 강도20 | `scoring.py`, 관측 가중치 재정규화·거래량 기준 메타데이터 |
| 09-04 `8fbffbe` | 뉴스 만점 기준 30→80건 | 뉴스 과대평가 문턱 조정; 현재는 span 없는 응답의 폴백 |
| 09-04 `a96f84c` | 일봉 오류 때 0.5초 뒤 1회 재시도 | Price `services/price.py`; 재실패 시 현재가 유지·VOLUME_BASELINE_UNAVAILABLE |
| 09-04 `33d725b` | 최근 30일 주요 공시와 이슈 키워드 연결 | matched 있으면 high, 주요 공시만 있으면 medium, 없으면 low |
| 09-04 `3643fac` | 뉴스 관심을 100건 축적 시간으로 변경 | 6시간 만점·168시간 0점·로그 스케일, span 없으면 80건 폴백 |
| 09-07 `94ee2d7` | 오류 분류·피드백·재검증·on 이력 재전송 | Runtime/Provider·단위시험, off 입력·직렬화 유지 |
| 09-07 `a5aa842` | 실제 비교 하네스·픽스처·원본·집계 | v1 120행 및 별도 Provider 2행 |
| 09-07 `52eff44` | 행동 지시·예측 패턴 v2 | off 재채점·on 60행 재실측, v1 원본 보존 |

커밋 내용은 `git log`와 `git show`로 확인했습니다. 이력의 각 변경을 이번 성찰 실험만으로 개별 인과 검증했다고 주장하지 않습니다. 현재 공시 매칭은 키워드 규칙이며 의미 유사도 모델이 아닙니다.

## 8. 프롬프트·파라미터 조정 이력

| 커밋 | 실제 변경 | 유지·검증 범위 |
| --- | --- | --- |
| `6f58007` | 추천/예측 금지·계산값 유지·출처·개인화 null·120자·2~3문장 지시 추가 | 모델 gpt-5.6-luna, low, 단계3, MCP15초·Workflow60초 |
| `6a3e779` | `NARRATIVE_STYLE_GUIDE` 결합, 해요체·성향별 문장·확인 우선순위 | 프롬프트 지시와 출력 Schema의 강제 상한은 별개 |
| `33d725b` | high/medium을 공시-이슈 매칭 의미로 변경, matched 공시명·날짜 안내 | 규칙 점수는 모델이 수정하지 않음 |
| `11b83ca` | low 근거 경고의 관심 온도 70→60 | 당시 온도 v2 반영 |
| `94ee2d7` | `agent_reflection_enabled=True`, `agent_max_reflections=2` 추가 | 기존 모델·reasoning·시간·단계 유지; Runtime 동적 피드백 추가 |
| `52eff44` | 프롬프트·Settings 변경 없음, 검증기·평가 수정 | 규칙 교체와 모델 재생성 효과 구분 |

근거 명령은 `git log -- mcp_client/app/prompts mcp_client/app/core/config.py`와 해당 커밋의 `git show`입니다. on에서만 최초 실패 정보를 추가한 Workflow 입력 차이도 7.1절에 공개했습니다.

## 9. 관련 시험과 재현 검증

[Backend narrative_source 분기 시험](agent-test-result-report_narrative-source.md)은 성공 서술 채택·실패 시 규칙 조립을 담당합니다. 해당 문서는 수정하지 않았습니다. 그 문서의 VPS 단일 표본 “조건부 PASS”를 재판정하지 않고, 미해결 다건 정량화를 이 보고서 6.4절에서 보완합니다.

이번 문서 확정 전 `/root/.venvs/team5-mcp-client/bin/python -m pytest -q`를 `mcp_client/`에서 실행해 122 passed, 같은 Python의 `-m pytest tests/contract -q`를 저장소 루트에서 실행해 2 passed를 확인했습니다. 모든 시험 출력에는 `[TEST]`를 붙였습니다. 서비스·Agent 코드는 이번 문서 작업에서 변경하지 않았습니다.

## 10. 결론

정상 입력, 빈 목록, 현재가 중단과 제한된 서술 성찰의 동작을 확인했습니다. v2에서 수급 사실 오탐이 줄고 채택된 모델 서술의 규칙 통과율은 상승했으나, 목표주가 문맥 오탐으로 모델 완료 1건을 잃었습니다. 상세 실패 복구는 실측 미도달이며, 다른 오류 유형의 복구는 단위시험 근거로만 남습니다. 운영 이력의 OpenAI 부분실패 포함률 33.60%는 별도 다건 관측이고, 새 성찰 루프의 운영 효과는 배포 후 추가 검증이 필요합니다.
