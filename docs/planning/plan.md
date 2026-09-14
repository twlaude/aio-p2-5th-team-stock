# 개발 계획 및 팀원 역할 분담

> **한눈에** — 다섯 담당 영역에서 일곱 서비스를 만듭니다.
> 연결 계약을 먼저 정하고, 각 서비스를 따로 개발합니다.
> 역할·완료 기준·일정·제출 범위를 정리합니다.

## 1. 팀 구성

| 이름 | 역할 |
|---|---|
| 권오현 (팀장) | 기획·아키텍처·계약 문서, MCP Client Agent Workflow(분석 처리 흐름), Price MCP(한국투자증권), 발표 |
| 문태웅 | React 프론트엔드 전체, Community MCP·커뮤니티 FGI(공포탐욕지수) 데이터 파이프라인, 통합 테스트·운영 |
| 윤기화 | Backend(인증·Memory·개인화·분석 API), DB·infra, News MCP |
| 김인혜 | Disclosure MCP(OpenDART 수집·사업보고서 RAG(검색 기반 생성)·pgvector(벡터 검색 확장)) |
| 박성엽 | 화면 흐름·문구·설명 검수, 사용성·발표 리허설 피드백 |

## 2. 작업 5덩어리

화면, 사용자·저장소, 분석 처리, 데이터 서버를 독립 실행합니다. 일곱 서비스의 포트·Endpoint·Tool·JSON 필드는 여러 담당자에게 영향을 줍니다. 구현 전에 `docs/specs/CONNECTION_CONTRACT.md`와 `docs/specs/contracts/`로 연결을 고정합니다.

## 3. 파트별 상세

| 영역·담당 | 맡는 파일·산출물 | 범위·완료 기준 |
|---|---|---|
| ① 기획·오케스트레이션·가격 — 권오현 | `docs/`, `shared/`, `mcp_client/`, `mcp_servers/price_mcp/`. 기획·최종 아키텍처·연결 계약, 단일 Stock Analysis Agent Workflow, Price MCP(KIS), 발표 자료·시연 흐름 | 현재가·최근 뉴스·정기공시·최근 30일 주요 공시·사업보고서 검색·커뮤니티 반응의 6개 기본 조회를 정해진 방식으로 병렬 호출합니다. |
| Agent 경계 | [에이전트 아키텍처 설계서](../architecture/agent-architecture.md) | 기본 결과를 설명합니다. 기본 목록의 접수번호로 `get_disclosure_detail`만 최대 2건 추가 조회합니다. 모델은 최초 1회 + 후속 최대 3회 호출합니다. 서술 검증 실패 시 성찰 재호출 2회 이내로 교정하며, 넘으면 기본 서술로 끝냅니다. |
| 가격·분석 완료 | 한국투자증권 실전투자 REST 현재가, 종목별 60초 캐시 | API 실패를 가짜 가격으로 대체하지 않습니다. `POST /internal/v1/common-analyses`는 규칙 기반 관심 온도·근거 수준과 Agent 설명을 계약대로 반환합니다. 현재가 실패는 전체 실패, 나머지 Tool 실패는 확인된 자료를 유지한 부분 성공입니다. |
| ② 사용자 화면·Community·운영 — 문태웅 | `frontend/`, `mcp_servers/community_mcp/`, 운영 설정. React 검색·결과·로그인, 상태형 SVG 마스코트·반응형 화면, 반응·FGI Tool, 데모 환경·배포·통합 검증 | 검색 히어로 → 가격·한 줄 결론 → 비회원 게이트 → 회원 근거 → 성향별 확인 포인트의 단일 페이지와 `/login`을 만듭니다. |
| 데이터·화면 완료 | Community MCP에서 네이버 종목토론방 집계 FGI API 조회·정규화 | 원문 전체 대신 집계·주제·짧은 대표 근거를 전달합니다. 데스크톱·390px에서 가로 스크롤 없이 비회원·회원·미지원·부분 실패·전체 실패를 표시합니다. Frontend부터 네 MCP까지 한 요청이 왕복합니다. |
| ③ 사용자·저장소·뉴스 — 윤기화 | `backend/`, `db/`, `infra/`, `mcp_servers/news_mcp/`. FastAPI Backend, JWT(인증 토큰) 로그인·데모 사용자 10명·성향·장단기 Memory(기억)·개인화·분석 API·이력, PostgreSQL·Redis·Docker Compose, News MCP | Backend만 Frontend 요청을 받습니다. 지원 종목·회원 확인, 성향 조회, MCP Client 호출, 공개·회원 응답 조립을 맡습니다. |
| 저장·뉴스 완료 | PostgreSQL: 사용자·성향·분석 실행 이력. Redis: 최근 검색 상태와 TTL(보관 시간) | NAVER API HUB 뉴스를 정제해 최근 자료 우선 최대 10건을 반환합니다. 기사 본문 전체 크롤링은 제외합니다. 공개 범위를 분리하고 사용자별 JWT·성향·Memory를 격리합니다. `db/schema.sql`·`db/seed.sql`은 Compose 최초 실행에 적용합니다. |
| ④ 공시·사업보고서 RAG — 김인혜 | `mcp_servers/disclosure_mcp/`. 최근 공시·상세·사업보고서 검색·정기보고서 유형별 검색 Tool, OpenDART 수집기·보고서 파서·청커(구절 분할기)·pgvector 저장·검색 | 지원 20종목 기업코드를 동기화하고 최근 공시 메타데이터·최신 연간 사업보고서를 수집합니다. 기업·보고서 연도를 SQL로 좁히고 `text-embedding-3-small` 1536차원 벡터로 관련 구절 최대 5개를 찾습니다. |
| 공시 완료 | `get_recent_disclosures`, `get_disclosure_detail`, `search_annual_report`, `search_periodic_report` | 현재 Tool 계약을 지킵니다. MCP Client에 DART 원문 전체 대신 필요한 메타데이터·상세·관련 구절만 전달합니다. |
| ⑤ 사용자 관점 검수 — 박성엽 | 화면 흐름 점검표, 어려운 문구·설명 피드백, 리허설 관찰 결과 | 검색 시작·분석 대기·공개 결과·로그인 게이트·회원 근거·성향별 확인 포인트·미지원·오류 안내·발표 시연을 검수합니다. |
| 검수 완료 | 투자 추천 오해, 데이터 부족 은폐, 회원·비회원 경계 모호함을 우선 확인 | 처음 보는 사용자도 검색부터 근거 확인까지 진행합니다. 관심 온도가 상승 가능성이나 추천 점수가 아님을 이해합니다. |

## 4. 발표 준비 — 권오현(발표자)

| 항목 | 내용 |
|---|---|
| 구성·대본 | 문제·목적 → 일곱 서비스 → 네 MCP 데이터 흐름 → Workflow·Agent 경계 → Memory 개인화 → 실제 데모 → 한계. 대본은 비회원 삼성전자 검색 → `왜 이렇게 판단했나요?` 게이트 → 데모 로그인 → 근거·출처 → 성향별 확인 포인트 → 미지원 종목입니다. |
| 기술·안전망 | Frontend는 Backend만 호출합니다. MCP Client가 네 MCP를 통합하고 Agent는 읽기 전용 공시 상세 Tool만 제한 조회합니다. 네트워크·일부 MCP 실패는 부분 성공·규칙 기반 문장 폴백(대체 응답), 가격 부재는 분석 중단으로 설명합니다. |
| 리허설·사전 점검 | 실제 데모 환경에서 최소 2회 리허설합니다. 박성엽이 화면 전환·문구 이해도·설명 속도·질문 지점을 기록해 전달합니다. 발표 전 Frontend·Backend·MCP Client·MCP 4개의 `/health` 또는 상태 주소와 삼성전자 전체 왕복을 확인합니다. |

## 5. 협업 규칙

| 규칙 | 내용 |
|---|---|
| 브랜치·담당 | `main`은 통합 완료 상태로 유지합니다. 기능 브랜치는 PR 리뷰 후 병합합니다. 다른 담당 폴더 수정 전 영향 범위·계약 변경을 공유합니다. |
| 계약 | 포트·Endpoint·Tool·필드는 위 연결 계약 문서에서 먼저 합의합니다. 구현·테스트·문서를 함께 갱신합니다. |
| 사용자 정보 | MCP Client에는 성향 네 값만 전달합니다. 사용자 ID·비밀번호·JWT·개인정보는 금지하며, MCP 서버에는 성향도 전달하지 않습니다. |
| 비밀·데이터 | 실제 `.env`·API Key·DB 비밀번호·토큰은 커밋하지 않습니다. `.env.example`에는 이름·예시 형식만 둡니다. 미확인 값은 추측하지 않고 일부 실패는 `partial_success`·실패 목록으로 표시합니다. |
| 테스트·리뷰 | 서비스 단위 → 계약 → MCP 연결 → Backend 연결 → Frontend 시나리오 순입니다. 구현 담당자가 계약·코드 일치를 확인하고 문구·화면에는 박성엽 검수를 반영합니다. |

## 6. 일정

| 기간 | 목표·결과 |
|---|---|
| 2026-08-31 | 착수·범위 확정: 목적, 지원 20종목, 일곱 서비스 책임, 포트·폴더 구조 |
| 2026-09-01 | 계약·Mock(예시 응답)·저장소 뼈대: 연결·Tool·JSON 계약, PostgreSQL·Redis 스키마, Mock 응답·기본 화면 |
| 2026-09-02 | 핵심 구현: Backend 인증·성향·Memory, MCP Client Workflow, Price·News·Disclosure·Community MCP 독립 실행 |
| 2026-09-03 | 실제 데이터·Agent·화면 연결: 외부 제공처·RAG, Agent 제한, 공개·회원 흐름 완성 |
| 2026-09-04 | 통합·문서화: Frontend → Backend → MCP Client → MCP 4개 왕복, 실패·반응형·제출 문서 검증 |
| 발표 준비 기간 | 코드 동결 후 치명적 오류만 수정합니다. 대본·데모 데이터를 고정하고 리허설 피드백을 반영합니다. |
| 발표 | **발표일 확정 후 기입**. 저장소·문서·데모 주소를 최종 확인합니다. |

## 7. 제출

| 항목 | 내용 |
|---|---|
| 서비스·repo | `살래? 말래?` · `twlaude/aio-p2-5th-team-stock` (앙코르 AI 오케스트레이션 1기 · 2차 프로젝트 · 5팀). 기본 브랜치 `main`에는 통합 검증·리뷰 완료 결과만 반영합니다. |
| 실행 단위 | Frontend, Backend, MCP Client, Price·News·Disclosure·Community MCP의 일곱 서비스 |
| 필수 산출물 | `docs/specs/` API·DB·화면 설계서, `docs/planning/plan.md`, `docs/architecture/diagrams/` Mermaid 원본, `docs/architecture/agent-architecture.md`·`docs/reports/agent-test-report.md`, 루트 `README.md` |
| 기준·최종 확인 | `docs/architecture/FINAL_ARCHITECTURE.md`, `docs/specs/CONNECTION_CONTRACT.md`, `docs/specs/contracts/` 기준입니다. 문서 경로·링크, 고정 포트, 데모 계정, 비밀 값 미포함, Mermaid 문법, 전체 왕복·미지원·부분 실패를 확인합니다. |
