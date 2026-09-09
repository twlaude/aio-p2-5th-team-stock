# tests — 서비스 경계를 넘는 테스트

서비스 안의 단위 테스트는 각 폴더의 `tests/`에 있고(`backend/tests`, `mcp_client/tests`, `mcp_servers/*/tests`, `frontend/tests`), 여기에는 여러 서비스가 함께 지켜야 하는 것만 둡니다.

| 경로 | 내용 | 실행 |
|---|---|---|
| `contract/` | 고정 자산 계약. `shared/supported_companies.json`이 20종목·유일한지 등 | `python -m pytest -q tests/contract/` |
| `scenarios/agent_eval/` | Agent 시험 하네스. 실제 MCP 자료를 픽스처로 고정하고 동일 30케이스로 자기 성찰 off/on 비교 | 폴더의 `README.md` 순서대로 (`capture_fixtures` → `test_harness` → `run_eval` → `report`) |

실측 결과 보관본은 `docs/reports/agent-eval-results/`, 해석은 `docs/reports/agent-test-report.md`입니다.
