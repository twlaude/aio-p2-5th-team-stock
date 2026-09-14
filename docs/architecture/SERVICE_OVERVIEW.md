# 서비스 구조

**한눈에**

- Frontend·Backend·MCP Client·MCP 서버 4개, 총 7개를 독립 실행합니다.
- 화면은 Backend만, Backend는 MCP Client만 호출합니다. MCP 서버끼리는 호출하지 않으며 사용자 정보도 받지 않습니다.
- 호출 예산·개인화·저장 책임은 [최종 아키텍처](FINAL_ARCHITECTURE.md)에 정리했습니다.

<img src="../images/architecture.svg" alt="Frontend → Backend → MCP Client → Price·News·Disclosure·Community MCP" width="100%">

## 일곱 서비스의 책임

| 서비스·폴더 | 포트 | 역할 | 기술 |
| --- | ---: | --- | --- |
| Frontend · `frontend/` | 8501 | React 단일 페이지: 검색·로그인·공개 결과·근거·개인화 확인 포인트 | React 19, TypeScript, Vite 8, React Router, Motion, Lucide React |
| Backend · `backend/` | 8000 | 공개 API, 지원 기업, JWT(로그인 토큰), 투자 성향, Memory(저장된 사용자 맥락), 분석 이력, 접근 수준별·개인화 응답 | Python 3.12, FastAPI, Pydantic v2, PyJWT, psycopg2, Redis |
| MCP Client · `mcp_client/` | 8010 | 기본 Tool(조회 도구) 6개 병렬 호출 → 규칙 계산 → 단일 Agent(분석 에이전트) 실행, 네 MCP 통합·출처·부분 실패 취합 | FastAPI, FastMCP 4, OpenAI Responses API, `gpt-5.6-luna` |
| Price MCP · `mcp_servers/` | 8020 | 한국투자증권 Open API 현재가, 종목별 60초 캐시 | FastMCP Streamable HTTP, HTTPX |
| News MCP · `mcp_servers/` | 8021 | NAVER API HUB 최근 뉴스 정제, 중복·무관 기사 제외 | FastMCP Streamable HTTP, HTTPX |
| Disclosure MCP · `mcp_servers/` | 8022 | OpenDART 공시·사업보고서 RAG(자료 검색 후 답변 생성) | FastMCP Streamable HTTP, HTTPX |
| Community MCP · `mcp_servers/` | 8023 | 네이버 종목토론방 반응 집계·커뮤니티 FGI(공포탐욕지수) API 정규화 | FastMCP Streamable HTTP, HTTPX |
| DB · `db/` / 인프라 · `infra/` | — | Backend 스키마·시드·마이그레이션 / PostgreSQL·Redis Docker Compose | PostgreSQL, pgvector(벡터 검색 확장), `text-embedding-3-small` 1536차원 |
| 공유 · `shared/` / 테스트 · `tests/` | — | 서비스 연결 계약·지원 기업 Snapshot(목록 사본) / 계약·통합·발표 시나리오 | pytest, Vitest, Playwright Core |
| 문서 · `docs/` | — | 전체 문서 | architecture·specs·planning·operations·reports |

## 요청과 설계 원칙

MCP Client는 관심 온도·근거 수준을 계산한 뒤 제한된 근거를 Agent에 전달합니다. Agent의 선택 Tool은 `get_disclosure_detail` 하나입니다.

| 설계 | 이유·규칙 |
| --- | --- |
| Frontend 단일 진입점 | Backend 주소 외의 비밀값을 넣지 않습니다. MCP·DB 주소와 사용자 성향 원본도 브라우저에 노출하지 않습니다. |
| 기본 조회와 Agent 분리 | Workflow가 필수 자료를 항상 조회해 재현성을 확보합니다. Agent 선택은 읽기 전용 공시 상세로 제한합니다. |
| 데이터 MCP 분리 | 제공처별 인증·오류·캐시·정제를 독립 관리합니다. |
| 공통 분석과 개인화 분리 | 같은 종목의 공통 근거를 유지합니다. 회원 성향은 확인 순서·설명 난이도에만 씁니다. |
| 부분 성공 | 뉴스·공시·커뮤니티 일부 실패 시 확인된 결과·실패 목록을 함께 반환합니다. 필수 현재가 실패 시 분석을 중단합니다. |
| 정형·벡터 검색 분리 | SQL로 지원 기업·보고서 범위를 좁힌 뒤 pgvector로 관련 구절을 찾습니다. |
| 출처와 시간 유지 | 미확인 값을 추측하지 않습니다. 수집 시각·공식 URL을 남깁니다. |
| 비밀·인증 보호 | 실제 `.env`·API Key·DB 비밀번호·내부 토큰은 Git에 올리지 않습니다. 비밀번호는 PBKDF2 해시, 로그인은 만료 시간이 있는 HS256 JWT를 사용합니다. |
| 사용자 정보 보호 | MCP Client에 사용자 ID·비밀번호·JWT를, 네 MCP 서버에 투자 성향을 보내지 않습니다. Memory에 인증정보·API Key를 저장하지 않습니다. |
| LLM(언어 모델) 입력 제한 | 원본 전체 대신 제한된 기사·보고서 구절·커뮤니티 집계만 전달합니다. |

## 상세

- Backend: 라우터는 HTTP 입력·출력, 서비스는 인증·성향·Memory·분석 조립, `repositories/`는 저장소, `clients/`는 외부 통신을 맡습니다. Pydantic Schema·Core·PostgreSQL·Redis·MCP Client 연결: [Mermaid 원본](diagrams/backend-architecture.mmd), [SVG](diagrams/backend-architecture.svg), [다크 SVG](diagrams/backend-architecture-dark.svg).
- 전체 시스템 구성: [Mermaid 원본](diagrams/system-topology.mmd), [SVG](diagrams/system-topology.svg), [다크 SVG](diagrams/system-topology-dark.svg).
- Agent 최신 분기·성찰·종료 조건과 논리 Tool/실제 MCP 이름: [에이전트 설계서](agent-architecture.md), [상태 흐름도](diagrams/agent-state-flow.mmd).
- 실행법·하위 구조·환경변수: `backend/`, `mcp_client/`, `mcp_servers/`, `frontend/`, `shared/`, `db/`, `infra/`, `tests/` 각 폴더의 `README.md`.
