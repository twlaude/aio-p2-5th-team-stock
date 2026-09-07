# 보관 문서·산출물 색인

개발 과정에서 나온 시안·초기 설계·실험 결과·옛 코드를 한곳에 모아 둔 폴더입니다. 현재 구현 기준은 `docs/architecture/`·`docs/specs/`·각 실행 폴더의 `GUIDE.md`이고, 여기 있는 것은 참고용입니다.

| 현재 위치 | 원래 위치 | 내용 | 옮긴 날 |
|---|---|---|---|
| `design-drafts/` | 루트 `doc/이미지/` | 화면 시안 이미지 4장 (검색·로그인·요약·상세) | 2026-09-07 (603b5f7) |
| `image-prompts/` | 루트 `text/프롬프트/` | 시안 이미지 생성 프롬프트 5개 | 2026-09-02 (2f338ec) |
| `initial-design/` | 루트 `gide/` | 2026-09-02 구조 확정 전 아이디어·대안 비교·폴더 제안서 00~07 | 2026-09-02 (2f338ec) |
| `eval-results/agent_eval/` | `tests/scenarios/agent_eval/results/` | 에이전트 성찰 루프 off/on 실측 결과 (v2·round1·context-v3 jsonl, summary.md). `docs/reports/agent-test-report.md`가 참조 | 2026-09-07 |
| `legacy-code/stock_mcp/` | 루트 `archive/legacy/stock_mcp/` | 프로젝트 초기의 단일 MCP 서버 골격. 현재는 `mcp_client` + `mcp_servers/*` 4개 구조 | 2026-09-07 |

- 실험을 다시 돌리면 결과는 `tests/scenarios/agent_eval/results/`에 새로 생기고 git에 올라가지 않습니다(`.gitignore`). 보고서에 쓸 결과만 이 폴더로 옮겨 주세요.
- `legacy-code/`는 실행·확장하지 않습니다. 필요한 코드만 참고합니다.
