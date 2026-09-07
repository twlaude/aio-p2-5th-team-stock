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
