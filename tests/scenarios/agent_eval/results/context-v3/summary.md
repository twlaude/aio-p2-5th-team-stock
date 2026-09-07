# 검증기 v3·상세 실패 보조 검증 (fix_plan 4)

2026-09-07에 수행한 별도 보조 검증입니다. 기존 [v2 비교 결과](../summary.md)의 30케이스·120행과 수치를 보존합니다.
이번 결과는 자연 선택 정확도, 실제 MCP 장애 복구율, 성찰의 운영 개선 효과를 의미하지 않습니다.

## 1. 검증 규칙과 시험 설계

`v3_context_patterns`는 목표주가의 명시적 비제시·미확인 표현을 같은 절 안에서 구분합니다.
직접 인용은 따옴표 앞의 가장 가까운 출처가 뉴스·공시·커뮤니티 중 무엇인지 확인하고,
해당 수집 자료에 인용 원문이 있는 경우에만 허용합니다. 공백만 정규화하며 수치·문구를 바꿔 추정하지 않습니다.
인용문 밖의 목표주가나 매수 지시, 부정문 뒤의 가격 추천, 이중 부정은 별도로 검출합니다.

실패 소스의 요약은 확인 불가·미수집·미제공·조회 오류·표본 부재의 동등 표현을 인정합니다.
가장 가까운 출처가 다른 소스인 제한 안내, 임상 실패 등 사업 사건, `실패 없이`는 제한 안내가 아닙니다.
단위시험은 원문·수치·출처가 다른 인용, 부정과 추천의 혼합, 한글 금액, 다른 소스의 실패를 포함합니다.

실제 상세 호출을 확인하기 위해 기존 `detail_failure-01` 삼성전자 픽스처를 사용했습니다.
첫 실제 OpenAI 요청에만 `tool_choice={"type":"function","name":"get_disclosure_detail"}`을 지정했습니다.
모델이 선택한 허용 접수번호를 실제 Runtime이 검증·호출한 뒤 FixtureCollector가 `injected_failure`를 발생시켰습니다.
후속 호출은 기존 off/on Provider 이력 처리·도구 선택·성찰 상한을 유지했습니다. 실제 MCP 접속은 없습니다.

## 2. 실제 Provider·Runtime 보조 실행 결과

모델은 `gpt-5.6-luna`이며 각 모드를 1회씩 순차 실행했습니다. 입력 픽스처·주입 해시는 두 모드가 같습니다.

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

off는 후속 HTTP 400 `previous_response_not_found`로 종료했습니다. 기존 `store=False`와 `previous_response_id`
전달 경로의 실제 실패이며, 폴백에 공시 상세 실패 제한이 없다는 점도 외부 verifier에 남았습니다.
on은 요청 내 이력과 `function_call_output`을 재전송하고 다음 서술을 채택했습니다.

> 자기주식취득결정 공시의 상세 내용은 조회에 실패했어요.

상세 조회 자체는 복구되지 않았습니다. 성공한 목록 자료와 상세 실패 제한을 담은 모델 설명이 채택된 것입니다.
성찰 재호출이 0회이므로 이 실측에서 서술 수정 성찰의 효과를 주장하지 않습니다.
수정 성찰은 MockTransport 시험에서 제한 누락 → 피드백 → 수정 응답·해소 이벤트로 별도 검증했습니다.

원본: [off 1행](detail_failure_off.jsonl), [on 1행](detail_failure_on.jsonl).
각 행에는 컨텍스트, 실제 Tool 인자, 후속 실패 피드백, API 오류, 모델 서술, Provider·HTTP·성찰 횟수가 있습니다.
`failure_feedback_delivered`는 Provider 후속 진입을 뜻하며 HTTP 성공이 아닙니다.
`recovery_completed`는 상세 실패 도달·후속 진입·Agent completed·최종 verifier 통과를 모두 요구합니다.
두 행 모두 `excluded_from_metrics=true`, `included_in_metrics=false`이며 기존 비교 지표에 합산하지 않습니다.

## 3. 저장된 v2 서술의 오프라인 재검사

[verifier_audit.jsonl](verifier_audit.jsonl)은 v2 off/on 120행의 원본 파일·서술 SHA-256, 원래 종료 사유,
원래 verifier 결과와 v3 결과를 함께 기록합니다. 추가 LLM·HTTP 호출은 모두 0회입니다.
원본 서술·종료 사유·호출 횟수·원본 JSONL 파일은 변경하지 않았습니다.

| 대상 | 저장된 모델 완료 / 평가 대상 | v2 규칙 통과 / 완료 | v3 규칙 통과 / 같은 완료 |
|---|---:|---:|---:|
| off | 56 / 56 | 43 / 56 (76.79%) | 54 / 56 (96.43%) |
| on | 55 / 56 | 55 / 55 (100.00%) | 55 / 55 (100.00%) |

각 모드의 현재가 실패 4행은 원래처럼 분모에서 제외합니다. off의 실패 제한 누락 판정 12건은 모두 해소됐으나,
그중 1건에 목표주가 표현도 있어 전체 통과 증가는 11건입니다. 남은 off 위반은 `normal-09/2`,
`community_failure-03/2`의 간접적인 목표주가 언급입니다. 직접 인용 예외를 간접 인용으로 확대하지 않았습니다.
on의 과거 성찰 소진 1건은 그대로 미완료입니다. 재검사는 모델 완료율 개선이나 새 on 실측이 아닙니다.

## 4. 검증·재현·한계

- MCP Client: `cd mcp_client && /root/.venvs/team5-mcp-client/bin/python -m pytest -q` → 183 passed, 기존 Starlette 의존성 경고 1건.
- 계약: 저장소 루트 `.../python -m pytest tests/contract -q` → 2 passed.
- 하네스: 저장소 루트 `.../python -m pytest tests/scenarios/agent_eval/test_harness.py -q` → 21 passed.
- 위 계약·하네스의 최종 합동 실행은 23 passed입니다. 모든 출력에 `[TEST]`를 붙였습니다.
- MockTransport 4건: off/on 정상 실패 안내, on 제한 누락 후 성찰 수정, off 후속 HTTP 400.
- 실제 API 보조 실행 명령은 [하네스 README](../../README.md)의 v3 절에 있습니다. 기존 파일이 있으면 실행을 거부합니다.

오프라인 재검사 파일은 다음과 같이 네트워크 없이 원본과 대조할 수 있습니다. 저장소 루트에서 실행합니다.

```bash
PYTHONPATH=mcp_client /root/.venvs/team5-mcp-client/bin/python - <<'PY'
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
print('[TEST] 120 offline verifier observations match source and current rules')
PY
```

이 검증기는 제한된 한국어 패턴입니다. 수치를 담은 부정문·간접 인용·출처를 뒤에 쓰는 인용은 보수적으로 거절할 수 있습니다.
가장 가까운 출처명은 완전한 문법 분석을 대신하지 않습니다. 일반적인 사실 일치나 모든 투자 표현을 증명하지 않습니다.
이번 새 실측 2행은 첫 함수를 강제한 입력 개입이 있으므로 자연 선택 정확도·일반적인 복구율의 분모로 쓰지 않습니다.
운영 반영과 배포 후 표본 수집은 수행하지 않았습니다.
