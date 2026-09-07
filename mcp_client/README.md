# mcp_client — 분석 조립과 Agent 실행 (FastAPI, 포트 8010)

Backend에서 종목 하나를 받아 네 MCP 서버를 병렬 호출하고, 규칙으로 관심 온도·근거 수준을 계산한 뒤, 단일 Stock Analysis Agent가 제한된 근거만으로 설명을 만들어 돌려줍니다. 사용자 ID·비밀번호·JWT는 받지 않습니다.

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env            # OPENAI_API_KEY, 네 MCP URL
python server.py
python -m pytest -q tests/
curl http://localhost:8010/internal/v1/mcp-status   # 네 MCP 연결 확인
```

## 폴더 지도

| 경로 | 역할 |
|---|---|
| `server.py` · `app/main.py` | 진입점, 라우터 등록 |
| `app/api/routes.py` | `/health` · `/internal/v1/mcp-status` · `POST /internal/v1/common-analyses` |
| `app/workflows/analysis.py` | 규칙 기반 Workflow. 수집 → 계산 → Agent → 응답 조립 순서를 고정 |
| `app/services/data_collector/` | 기본 Tool 6개 병렬 호출, 부분 실패를 결과에 표시 |
| `app/services/analysis_builder/` | `scoring`(관심 온도) · `issues`/`matching`(30일 주요 공시 ↔ 현재 이슈 매칭 = 근거 수준) · `sources`(출처 취합) · `narrative`(설명 입력 정리) |
| `app/agents/` · `app/runtime/` | Agent 정의(`stock_analysis.py`), 도구 위험 정책(`policy.py`), 실행 루프·자기 성찰(`runtime/agent.py`, `verifier.py`) |
| `app/prompts/` | Agent 프롬프트와 서술 스타일 |
| `app/providers/openai.py` | LLM 호출 (Responses API) |
| `app/clients/` | MCP 서버별 HTTP 클라이언트 (`price`·`news`·`disclosure`·`community`) |
| `app/schemas/analysis.py` | Backend와 주고받는 응답 계약 |
| `app/services/progress_reporter.py` | 진행 이벤트를 Backend로 전달 (`BACKEND_EVENT_URL`) |

## 환경변수 요점

- `PRICE_MCP_URL` `NEWS_MCP_URL` `DISCLOSURE_MCP_URL` `COMMUNITY_MCP_URL` — 기본 8020~8023
- `OPENAI_MODEL` · `OPENAI_REASONING_EFFORT` · `MAX_AGENT_STEPS` — Agent 실행 상한
- `WORKFLOW_TIMEOUT_SECONDS` · `MCP_REQUEST_TIMEOUT_SECONDS` — 한 요청의 시간 제한
