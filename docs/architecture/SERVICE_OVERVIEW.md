# 서비스 구조

루트 README에서 옮겨 온 상세 설명입니다. 서비스 책임, 요청 흐름, Backend 계층, 설계 의도, 기술 스택, 폴더 구조, 보안 원칙을 다룹니다.

Frontend, Backend, MCP Client, 네 MCP 서버를 각각 독립 실행 단위로 분리했습니다. Frontend는 Backend만 호출하고 Backend는 MCP Client 한 곳만 호출합니다. 데이터별 MCP 서버는 서로 직접 호출하지 않으며 사용자 정보도 받지 않습니다.

<a href="docs/architecture/diagrams/system-topology.svg"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/architecture/diagrams/system-topology-dark.svg"><img src="docs/architecture/diagrams/system-topology.svg" alt="시스템 구성도" width="100%"></picture></a>

[시스템 구성도 Mermaid 원본](docs/architecture/diagrams/system-topology.mmd)

### 일곱 서비스의 책임

| 서비스         | 포트 | 책임                                                                         |
| -------------- | ---: | ---------------------------------------------------------------------------- |
| Frontend       | 8501 | 검색, 로그인, 공개 결과, 근거, 개인화 확인 포인트를 표시합니다               |
| Backend        | 8000 | 지원 기업, JWT, 투자 성향, Memory, 분석 이력과 접근 수준별 응답을 담당합니다 |
| MCP Client     | 8010 | 기본 Tool 병렬 호출, 규칙 계산, Agent 실행, 출처·부분 실패 취합을 담당합니다 |
| Price MCP      | 8020 | 한국투자증권 Open API의 현재가를 조회하고 종목별 60초 캐시를 적용합니다      |
| News MCP       | 8021 | NAVER API HUB의 최근 뉴스를 정제하고 중복·무관 기사를 제외합니다             |
| Disclosure MCP | 8022 | OpenDART 공시와 사업보고서 RAG를 제공합니다                                  |
| Community MCP  | 8023 | 네이버 종목토론방 기반 반응 집계와 FGI를 정규화합니다                        |

### 요청 한 건의 흐름

사용자 요청은 Frontend → Backend → MCP Client 순으로 이동합니다. MCP Client가 기본 Tool 6개를 병렬 호출하고 관심 온도·근거 수준을 계산한 뒤 Agent에 제한된 근거를 전달합니다. Agent가 선택하는 Tool은 `get_disclosure_detail` 하나입니다. 최신 분기·성찰·종료 조건과 논리 Tool/실제 MCP 이름의 구분은 [에이전트 설계서](docs/architecture/agent-architecture.md)와 [상태 흐름도](docs/architecture/diagrams/agent-state-flow.mmd)에 정리했습니다.

### Backend 계층

라우터는 HTTP 입력·출력을 처리하고, 서비스는 인증·성향·Memory·분석 조립을 수행합니다. 저장소와 외부 통신은 `repositories/`와 `clients/`로 분리했습니다. Pydantic Schema, Core, PostgreSQL·Redis·MCP Client의 자세한 연결은 [Backend 아키텍처](docs/architecture/diagrams/backend-architecture.mmd)에서 확인할 수 있습니다.

<a href="docs/architecture/diagrams/backend-architecture.svg"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/architecture/diagrams/backend-architecture-dark.svg"><img src="docs/architecture/diagrams/backend-architecture.svg" alt="Backend 계층 구조" width="100%"></picture></a>

### 설계 의도

| 설계                    | 이유                                                                                                                         |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Frontend의 단일 진입점  | 브라우저에 MCP 주소, DB 주소, 사용자 성향 원본과 비밀값을 노출하지 않습니다                                                  |
| 기본 조회와 Agent 분리  | 필수 자료는 Workflow가 항상 조회해 결과의 재현성을 확보하고, Agent의 Tool 선택 범위는 읽기 전용 공시 상세로 제한합니다       |
| 데이터 MCP 분리         | 제공처별 인증·오류·캐시·정제 규칙을 독립적으로 관리합니다                                                                    |
| 공통 분석과 개인화 분리 | 같은 종목의 공통 근거는 유지하고, 회원 성향은 확인 순서와 설명 난이도에만 사용합니다                                         |
| 부분 성공 유지          | 뉴스·공시·커뮤니티 일부가 실패해도 확인된 결과와 실패 목록을 함께 반환합니다. 단, 현재가는 필수라 실패하면 분석을 중단합니다 |
| 정형·벡터 검색 분리     | 지원 기업과 보고서 범위를 SQL로 먼저 좁힌 뒤 pgvector로 관련 구절만 검색합니다                                               |
| 출처와 시간 유지        | 확인하지 못한 값을 추측하지 않고, 수집 시각과 공식 URL을 결과에 남깁니다                                                     |

### 기술 스택

| 구분         | 사용 기술                                                        |
| ------------ | ---------------------------------------------------------------- |
| Frontend     | React 19, TypeScript, Vite 8, React Router, Motion, Lucide React |
| Backend      | Python 3.12, FastAPI, Pydantic v2, PyJWT, psycopg2, Redis        |
| MCP Client   | FastAPI, FastMCP 4, OpenAI Responses API, `gpt-5.6-luna`         |
| MCP 서버     | FastMCP Streamable HTTP, HTTPX                                   |
| 데이터베이스 | PostgreSQL, pgvector, `text-embedding-3-small` 1536차원          |
| 외부 데이터  | 한국투자증권 Open API, NAVER API HUB, OpenDART, 커뮤니티 FGI API |
| 인프라       | PostgreSQL·Redis Docker Compose, 서비스 7개는 각각 독립 실행     |
| 테스트       | pytest, Vitest, Playwright Core                                  |

### 폴더 구조

```text
├── frontend/       React 단일 페이지 사용자 화면
├── backend/        공개 API, JWT, 투자 성향, Memory, 개인화 응답
├── mcp_client/     기본 Workflow, 단일 Agent, 네 MCP 통합
├── mcp_servers/    Price · News · Disclosure · Community MCP
├── db/             Backend PostgreSQL 스키마·시드·마이그레이션
├── infra/          PostgreSQL/pgvector · Redis Docker Compose
├── shared/         서비스 연결 계약과 지원 기업 Snapshot
├── tests/          계약·통합·발표 시나리오 테스트
└── docs/           문서 전부 (architecture·specs·planning·operations·reports)
```

각 폴더의 실행법·하위 구조·환경변수는 그 폴더의 `README.md`에 있습니다 (`backend/`, `mcp_client/`, `mcp_servers/`, `frontend/`, `shared/`, `db/`, `infra/`, `tests/`).

### 보안 원칙

- 실제 `.env`, API Key, DB 비밀번호와 내부 토큰은 Git에 올리지 않습니다.
- Frontend에는 Backend 주소 외의 비밀값을 넣지 않습니다.
- 비밀번호는 원문이 아니라 PBKDF2 해시로 저장하고, 로그인은 만료 시간이 있는 HS256 JWT를 사용합니다.
- MCP Client에는 사용자 ID·비밀번호·JWT를 보내지 않으며, 네 MCP 서버에는 투자 성향도 보내지 않습니다.
- Memory에는 인증정보나 API Key를 저장하지 않습니다.
- LLM 입력에는 원본 전체가 아니라 제한된 기사, 보고서 구절, 커뮤니티 집계만 전달합니다.
