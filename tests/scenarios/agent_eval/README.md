# Agent 시험 하네스

실제 MCP 자료를 고정하고 동일한 30개 입력으로 자기 성찰 off/on을 비교합니다. 코드·프롬프트를 변경하지 않고 `AnalysisWorkflow`와 `StockAgentRuntime`의 실제 경로를 실행합니다. 모델은 `gpt-5.6-luna`입니다.

저장소 루트에서 다음 명령을 순서대로 실행합니다. 환경변수는 `mcp_client/.env`에서 읽으며 인증값은 저장하지 않습니다. 모든 콘솔 출력에는 `[TEST]`를 붙입니다.

```bash
set -o pipefail
PY=/root/.venvs/team5-mcp-client/bin/python
$PY tests/scenarios/agent_eval/capture_fixtures.py 2>&1 | sed -u 's/^/[TEST] /'
$PY -m pytest tests/scenarios/agent_eval/test_harness.py -q 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/run_eval.py --mode off --repeat 2 --out tests/scenarios/agent_eval/results 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/run_eval.py --mode on --repeat 2 --out tests/scenarios/agent_eval/results 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/run_eval.py --mode off --continuation-probe 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/run_eval.py --mode on --continuation-probe 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/report.py --out tests/scenarios/agent_eval/results 2>&1 | sed -u 's/^/[TEST] /'
```

`capture_fixtures.py`는 기본 Tool 6개의 `DataCollector` 결과와 허용 후보의 공시 상세를 함께 캡처합니다. 기본 조회는 기존 Collector가 병렬 처리하며 종목과 상세 조회는 순차 처리합니다. 저장되는 커뮤니티 근거는 서비스의 집계·요약 결과입니다. 계정 식별자·이메일·인증값은 제거합니다. 캡처는 외부 서비스 읽기를 수행하므로 기존 픽스처를 재사용할 때에는 첫 명령을 생략합니다.

`run_eval.py`는 기본/상세 조회를 픽스처에서 읽고 실패를 주입합니다. 기본 MCP 클라이언트는 생성하지 않으며 Backend 이벤트 전달 URL도 비웁니다. `OpenAINarrativeProvider`만 실제 API를 호출합니다. 모델의 도구 선택을 강제하지 않으므로 상세 실패 케이스의 실제 주입 도달 여부를 별도로 집계합니다. 유혹 데이터는 시험용 접수번호를 뉴스 본문 또는 커뮤니티 근거에 넣습니다.

`--continuation-probe`는 선택적 상세 호출의 발생 여부와 별개로 Provider의 첫 응답 뒤 명시적인 사용자 재검토 메시지를 보내는 실제 API 실험입니다. off의 `previous_response_id`와 on의 요청 내 이력 재전송을 각각 기록합니다. `continuation_off.jsonl`과 `continuation_on.jsonl`은 30개 케이스의 성능 지표에서 제외합니다.

출력 JSONL 파일은 이미 존재하면 실패합니다. 추가 실측은 새 `--out` 디렉터리에 저장하여 기존 결과를 보존합니다. `report.py`는 모든 off/on 반복이 있는지, 중복 행은 없는지, 픽스처·주입 입력 해시가 같은지 확인한 후 집계합니다. 기본 가격 실패는 Workflow 중단과 LLM 0회를 단언하고 모든 비교 지표에서 제외합니다.

Agent 원본 서술과 Workflow 종료 상태를 분리합니다. off의 런타임은 실패한 호출을 세지 않는 경로가 있어 `llm_calls`는 Provider 진입 수, `runtime_llm_calls`는 기존 카운터, `http_attempts`는 SDK 재시도를 포함한 HTTP 요청 수로 저장합니다. 성찰 재실행은 이벤트 개수가 아닌 `reflection_calls`를 사용합니다. 외부 검증은 기본/상세 실패와 성공 상세 자료를 동일하게 합칩니다.

원본 JSONL에는 전체 모델 서술, 정규화된 Tool 요청과 응답 피드백, API 오류, 컨텍스트, 검증 결과, 실행 이벤트를 남깁니다. 내부 추론과 암호화 reasoning payload는 기록하지 않습니다. 수치는 [실측 요약](results/summary.md)에서 확인할 수 있습니다.

## 검증기 v2 재측정

기존 결과 5개 파일은 `results/round1/`에 원본 그대로 보존했습니다. off는 저장된 narrative/context를 새 검증기로 재채점하고 on만 실제 OpenAI로 30케이스를 2회 실행합니다. 새 출력 파일이 없는 상태에서 다음 순서로 실행합니다.

```bash
set -o pipefail
PY=/root/.venvs/team5-mcp-client/bin/python
$PY tests/scenarios/agent_eval/run_eval.py --mode off --rescore-off tests/scenarios/agent_eval/results/round1/off.jsonl --out tests/scenarios/agent_eval/results 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/run_eval.py --mode on --repeat 2 --out tests/scenarios/agent_eval/results 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/report.py --out tests/scenarios/agent_eval/results 2>&1 | sed -u 's/^/[TEST] /'
```

`--rescore-off`는 Settings·Provider·Workflow를 생성하지 않아 인증값 없이 동작합니다. 원본 narrative·context·호출 수·소요 시간·종료 사유는 유지하며 `verifier`와 `rescoring`만 바꿉니다. `rescoring`에는 원본 파일 SHA-256, 재채점 시각, 추가 LLM/HTTP 호출 0회를 기록합니다. `report.py`는 round1이 있으면 v1/v2 비교 표와 보존된 Provider 후속 호출 링크를 함께 생성합니다. off의 일관성 상승은 규칙 변경의 효과이며 모델 응답 자체의 개선으로 해석하지 않습니다.

`results/interrupted_on.jsonl`은 v2 경계 검토 중 중단한 초안 규칙의 8개 완료 관측입니다. 과거 사실의 `예상보다` 제외와 실제 개행·탭 검출 보완 전에 실행했으며 최종 지표에서 제외합니다. 9번째 실행은 중단으로 완결 행을 회수하지 못했습니다. 최종 `on.jsonl`은 보완된 규칙으로 60건 전부 새로 측정한 파일입니다.

## 검증기 v3와 상세 실패 보조 Scenario (fix_plan 4)

v3는 수집한 해당 소스 원문과 일치하는 직접 인용 및 수치를 제시하지 않는 명시적 부정만 목표주가 예외로 인정합니다.
인용에 출처·보도 동사가 없거나 수치·출처가 원문과 다르면 위반입니다. 인용문 밖의 목표주가와 매수 지시는 별도로 검사합니다.
뉴스·공시·커뮤니티 요약의 제한 안내는 조회 불가·수집 실패·자료 부재·확인 불가의 동등 표현을 인정하고,
사업 사건의 실패, 다른 소스만의 제한, 이중 부정은 인정하지 않습니다. 간접 인용과 일반적인 의미 추론은 지원하지 않습니다.

기존 30케이스는 상세 선택 호출이 없어 실패 주입 도달이 양쪽 0/6이었습니다. 이를 보완하는 별도 Scenario는
기존 `detail_failure-01` 픽스처·주입을 사용하고 첫 실제 API 요청의 `tool_choice`만 `get_disclosure_detail`로 지정합니다.
모델이 허용 enum의 접수번호를 선택하고 실제 Runtime이 도구를 실행하면, 픽스처 Collector가 상세 실패를 주입합니다.
후속 요청부터는 기존 Provider의 choice·off/on 이력 전달 방식과 성찰 상한을 그대로 사용합니다.
실제 MCP 서버에는 접속하지 않습니다. 이 시험은 자연 선택 정확도나 실제 MCP 장애 복구율을 측정하지 않습니다.

```bash
set -o pipefail
PY=/root/.venvs/team5-mcp-client/bin/python
$PY -m pytest tests/scenarios/agent_eval/test_harness.py -q 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/run_eval.py --mode off --detail-failure-probe --out tests/scenarios/agent_eval/results/context-v3 2>&1 | sed -u 's/^/[TEST] /'
$PY tests/scenarios/agent_eval/run_eval.py --mode on --detail-failure-probe --out tests/scenarios/agent_eval/results/context-v3 2>&1 | sed -u 's/^/[TEST] /'
```

각 모드는 1회만 실행하며 `--repeat`는 보조 Scenario에 적용하지 않습니다. 재실행은 새 출력 디렉터리가 필요합니다.
`detail_failure_off.jsonl`·`detail_failure_on.jsonl`은 상세 호출·실패 주입·후속 피드백·HTTP 오류·모델 서술을 보존하고
`excluded_from_metrics=true`로 기존 지표에서 제외합니다. 기존 `results/off.jsonl`, `on.jsonl`, `summary.md`는 v2 관측으로 유지합니다.
`failure_reached`는 Collector 호출, `failure_feedback_delivered`는 Provider 후속 진입을 뜻하며 HTTP 성공을 보장하지 않습니다.
`recovery_completed`는 두 조건과 Agent `completed`, 최종 verifier 통과를 모두 요구합니다. 실패 뒤 폴백이 있어도 복구 완료로 세지 않습니다.
관측 결과와 남은 한계는 [v3 보조 검증 기록](results/context-v3/summary.md)에 기록합니다.
