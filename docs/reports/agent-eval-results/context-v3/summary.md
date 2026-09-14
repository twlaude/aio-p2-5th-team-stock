# 검증기 v3·상세 실패 보조 검증

> **한눈에** — 2026-09-07, 상세 실패를 주입해 off/on을 각 1회 비교했습니다.
> off는 HTTP 400, on은 실패 안내를 채택했습니다. 상세 조회는 복구되지 않았습니다.
> v2 서술 재검사는 규칙 변화이며, 자연 선택·MCP 복구율·성찰 운영 효과가 아닙니다.

## 2. 실제 Provider·Runtime 보조 실행 결과

`gpt-5.6-luna`로 순차 실행했습니다. 픽스처(저장 입력)·주입 해시는 같습니다.

| 항목 | off | on |
|---|---|---|
| 시작 시각(KST) | 2026-09-07 14:05:04 | 2026-09-07 14:05:39 |
| 선택 접수번호 | 20260821000616 | 20260821000616 |
| 실제 Runtime 상세 호출 / 실패 주입 | 1 / 1 | 1 / 1 |
| Provider 진입 / 실제 HTTP 요청 | 2 / 2 | 2 / 2 |
| Runtime LLM 카운터 | 1 | 2 |
| 성찰 재호출 | 0 | 0 |
| 실패 피드백을 포함한 후속 진입 | 확인 | 확인 |
| Agent 종료 | model_error | completed |
| Workflow 종료 | model_error | partial_completed |
| 최종 서술 verifier 통과 | 아니요 | 예 |
| 실패 안내를 포함한 모델 응답 채택 | 아니요 | 예 |

off는 `store=False`·`previous_response_id` 후속 경로에서 HTTP 400 `previous_response_not_found`로 끝났습니다.
폴백의 상세 공시 실패 안내 누락도 외부 verifier(서술 검증기)에 기록했습니다.
on은 요청 이력·`function_call_output`을 재전송해 성공 목록과 상세 실패 안내를 채택했습니다.

> 자기주식취득결정 공시의 상세 내용은 조회에 실패했어요.

성찰 재호출 0회입니다. 수정 성찰은 별도 MockTransport의 제한 누락→피드백→수정 응답·해소 이벤트로 확인했습니다.

원본 [off 1행](detail_failure_off.jsonl)·[on 1행](detail_failure_on.jsonl): 컨텍스트·실제 Tool 인자·후속 실패 피드백·API 오류·모델 서술·Provider/HTTP/성찰 횟수입니다.

| 원본 필드 | 의미 |
|---|---|
| `failure_feedback_delivered` | Provider 후속 진입. HTTP 성공과 구분 |
| `recovery_completed` | 상세 실패 도달·후속 진입·Agent completed·최종 verifier 통과 모두 충족 |

두 행은 `excluded_from_metrics=true`, `included_in_metrics=false`입니다. [v2](../summary.md) 30케이스·120행 지표는 유지합니다.

## 3. 저장된 v2 서술의 오프라인 재검사

| 대상 | 저장된 모델 완료 / 평가 대상 | v2 규칙 통과 / 완료 | v3 규칙 통과 / 같은 완료 |
|---|---:|---:|---:|
| off | 56 / 56 | 43 / 56 (76.79%) | 54 / 56 (96.43%) |
| on | 55 / 56 | 55 / 55 (100.00%) | 55 / 55 (100.00%) |

[verifier_audit.jsonl](verifier_audit.jsonl)은 120행의 원본 파일·서술 SHA-256, 기존 종료 사유·verifier와 v3 결과를 기록합니다.
추가 LLM·HTTP는 0회이며 원본 서술·종료·호출 수·JSONL은 그대로입니다.
현재가 실패는 각 4행 제외합니다. off 제한 누락 12건은 해소됐으나 1건은 목표주가도 있어 통과는 11건 늘었습니다.
남은 `normal-09/2`·`community_failure-03/2`는 간접 목표주가 인용입니다. 직접 인용 예외를 확대하지 않았습니다.
on 성찰 소진 1건은 미완료로 유지합니다. 모델 완료율 개선·새 on 실측은 아닙니다.

## 1. 검증 규칙과 시험 설계

`v3_context_patterns`의 검사 기준입니다.

| 대상 | 규칙 |
|---|---|
| 목표주가 | 같은 절의 명시적 비제시·미확인 구분. 인용 밖 목표주가/매수 지시·부정 뒤 가격 추천·이중 부정 검출 |
| 직접 인용 | 따옴표 앞 가장 가까운 뉴스·공시·커뮤니티 출처의 수집 원문과 일치. 공백만 정규화, 수치·문구 추정 금지 |
| 실패 소스 제한 | 확인 불가·미수집·미제공·조회 오류·표본 부재 인정. 다른 소스 제한·임상 실패 등 사업 사건·`실패 없이` 제외 |
| 단위시험 | 원문/수치/출처가 다른 인용·부정과 추천 혼합·한글 금액·다른 소스 실패 |

삼성전자 `detail_failure-01`의 첫 OpenAI 요청만 `tool_choice={"type":"function","name":"get_disclosure_detail"}`로 강제했습니다.
Runtime이 모델의 허용 접수번호를 검증·호출하고 FixtureCollector가 `injected_failure`를 냈습니다.
후속 off/on Provider 이력·도구 선택·성찰 상한은 유지합니다. 실제 MCP 접속은 없습니다.

## 4. 검증·재현·한계

| 검증 | 명령·결과 |
|---|---|
| MCP Client | `cd mcp_client && .venv/bin/python -m pytest -q` → 183 passed, 기존 Starlette 의존성 경고 1건 |
| 루트 계약 | `.../python -m pytest tests/contract -q` → 2 passed |
| 루트 하네스 | `.../python -m pytest tests/scenarios/agent_eval/test_harness.py -q` → 21 passed, 계약 합동 23 passed |
| MockTransport 4건 | off/on 정상 실패 안내, on 제한 누락 후 수정 성찰, off 후속 HTTP 400 |

[하네스 README v3](../../../../tests/scenarios/agent_eval/README.md)의 실제 API 보조 명령은 기존 파일이 있으면 거부합니다.

한국어 패턴 검사는 수치 부정문·간접 인용·출처 후치 인용을 거절할 수 있습니다.
최근접 출처만으로 문법·모든 사실·투자 표현을 검증할 수 없습니다.
함수 강제 2행은 자연 선택·일반 복구율 분모에 쓰지 않습니다. 운영 반영·배포 후 표본 수집은 없습니다.

## 상세

상세 대조는 저장소 루트에서 네트워크 없이 실행합니다.

```bash
PYTHONPATH=mcp_client mcp_client/.venv/bin/python - <<'PY'
from pathlib import Path
from dataclasses import asdict
import hashlib, json
from app.runtime.verifier import verify_narrative
from app.schemas.analysis import Narrative
root = Path('tests/scenarios/agent_eval/results')
for line in (root / 'context-v3/verifier_audit.jsonl').read_text().splitlines():
    audit = json.loads(line)
    content = (root / f"{audit['mode']}.jsonl").read_bytes()
    assert hashlib.sha256(content).hexdigest() == audit['source_sha256']
    row = next(row for row in map(json.loads, content.splitlines())
               if (row['case_id'], row['repeat']) == (audit['case_id'], audit['repeat']))
    narrative = row['narrative']
    violations = [asdict(v) for v in verify_narrative(Narrative.model_validate(narrative), row['context'])] if narrative else []
    assert violations == audit['verifier']['violations']
print('120 offline verifier observations match source and current rules')
PY
```
