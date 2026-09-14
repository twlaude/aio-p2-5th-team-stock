# 최종 아키텍처

**한눈에**

- 지원 종목의 가격·뉴스·기업보고서·커뮤니티를 모아 상황과 근거를 설명합니다. 투자 결정을 대신하지 않습니다.
- Frontend → Backend → MCP Client → MCP 서버 4개로 연결합니다. [전체 구조도](SERVICE_OVERVIEW.md)를 참고합니다.
- 2026-09-07 코드·연결 계약 기준입니다. 성찰 브랜치 구현과 live 환경 배포 상태는 구분합니다.

## 1. 서비스 목적

지원 기업은 20개입니다. 자동 매수·매도 추천, 목표주가·수익률 예측, 상위 20개 밖 종목 분석은 제공하지 않습니다.

## 2. 전체 흐름

| 단계 | 확정 동작 |
| --- | --- |
| Backend | 지원 기업·비회원/회원 확인 → 회원 투자 성향·Memory(저장된 사용자 맥락) 조회 |
| MCP Client | 결정적 Workflow(정해진 수집·계산 흐름) → Stock Analysis Agent(분석 에이전트) 1개 → 네 MCP 결과 취합·공통 분석 |
| 기본 조회 | `get_stock_quote`, `search_news`, `get_recent_disclosures`, `get_material_disclosures`, `search_annual_report`, `get_community_reaction` 6개를 병렬 호출합니다. |
| 주요 공시 | 논리 작업 `get_material_disclosures`는 실제 MCP의 `get_recent_disclosures`에 30일·유형 필터를 전달합니다. |
| Agent 선택·예산 | 선택 Tool은 `get_disclosure_detail`뿐입니다. 모델 호출은 최초 1회 + 후속 최대 3회입니다. |
| 성찰 on | Runtime(실행 계층)이 상세 최대 2건·성찰 추가 호출 최대 2회를 강제합니다. |

## 3. 서비스 책임

| 서비스 | 담당 | 경계 |
| --- | --- | --- |
| Frontend | 검색·공개 결과·로그인·상세 근거·개인화 표시 | Backend만 호출합니다. API Key·DB 접속정보·투자 성향 원본을 관리하지 않습니다. |
| Backend | 지원 기업 20개, JWT(로그인 토큰) 로그인·회원가입, 데모 계정 10개, 성향·Memory 조회, 접근 수준별 응답 조립 | MCP Client에 성향 네 값을 선택 전달합니다. 성향 저장·수정·삭제를 맡습니다. |
| MCP Client | Price·News·Disclosure·Community MCP 발견·호출, 기본 조회 6개 정규화, 규칙 기반 관심 온도·근거 수준과 Agent 설명 생성 | Backend의 통합 호출 대상입니다. 외부 원본 API 직접 호출·원본 저장은 하지 않습니다. |
| MCP Client 입력 | `investment_profile`의 경험·위험 성향·투자 기간·선호 근거 → `personalized_checkpoints` | 사용자 ID·로그인 토큰·장기 Memory 원문은 받지 않습니다. |
| 네 MCP 서버 | 수집·검증·정제·출처 유지, 소스별 짧은 요약 | 최종 시장 온도·사용자 적합도를 판단하지 않습니다. 서로 호출하거나 사용자 정보를 받지 않습니다. |
| 데이터 연결 | Price → 실시간 가격 API, News → 최신 뉴스 API, Disclosure → DART + PostgreSQL/pgvector(벡터 검색 확장), Community → 커뮤니티 데이터 서버 | 제공처·포트·기술은 [서비스 구조](SERVICE_OVERVIEW.md)에 있습니다. |

## 5. LLM 사용 위치

| 항목 | 계약 |
| --- | --- |
| 공통 분석 | MCP Client가 제한된 자료·Python 계산 온도·근거 수준을 OpenAI `gpt-5.6-luna` LLM(언어 모델)에 전달합니다. `Narrative`의 strict JSON Schema(엄격한 출력 형식)를 따릅니다. |
| 모델 출력 | 공통 한 줄 설명, 뉴스·보고서·커뮤니티 요약, 성향이 있으면 개인화 확인 포인트·없으면 null입니다. |
| 규칙 출력 | Workflow가 온도·라벨·공식 근거 수준·출처·실패 목록을 조립합니다. 모델은 생성·변경하지 않습니다. |
| 근거 수준 | 최근 30일 주요 공시와 현재 이슈의 키워드를 매칭합니다. |
| 개인화 | Agent가 성향 네 값·수집 근거로 개인화 한 줄 설명, 먼저 확인할 항목 1~3개(Agent Schema), 주의할 점 1개를 만듭니다. |
| Backend 채택 | `agent_first`에서 OpenAI 실패가 없으면 Agent 서술·개인화를 채택합니다. 실패하거나 `NARRATIVE_SOURCE=backend`이면 규칙 기반 문장으로 대체합니다. |
| 성향 영향 | 온도·근거 수준 계산은 성향과 무관합니다. 성향이 같은 모델 요청에 들어가므로 공통 설명의 글자 단위 동일성은 보장하지 않습니다. |

## 6. 저장소 책임

| 데이터 | 책임 위치 |
| --- | --- |
| 사용자·투자 성향·장기 Memory / 세션·짧은 캐시 | Backend + PostgreSQL / Backend + Redis |
| 기업보고서 원문 메타데이터·임베딩(검색용 벡터) | Disclosure MCP + PostgreSQL/pgvector |
| 실시간 가격·뉴스 / 커뮤니티 집계 | 원본 API·필요 시 각 MCP의 짧은 캐시 / 외부 커뮤니티 서버·Community MCP 조회·변환 |
| 지원 기업 Snapshot(목록 사본) | `shared/supported_companies.json` |

MVP(최소 기능 제품)는 MCP별 PostgreSQL을 만들지 않습니다. PostgreSQL/pgvector 인스턴스 하나에서 테이블 책임을 나눕니다.

## 7. 화면 접근 수준

| 사용자 | 표시 순서 |
| --- | --- |
| 비회원 | 검색 → 기업명·가격·등락·공통 한 줄 설명 → 상세 클릭 시 회원가입 안내 |
| 회원 | 검색 → 비회원 결과 → 시장 온도·근거 요약·출처 → 성향별 확인 포인트 |

## 8. 이번 프로젝트에서 하지 않는 것

1절의 범위 제한에 더해 종목별 사용자 커뮤니티, Multi-Agent(여러 에이전트) 구조, 실제 증권 주문, 포트폴리오·매매내역 관리는 제공하지 않습니다.
관리자용 Backend 실황 페이지는 최근 검색·분석 이력·부분실패 집계를 표시합니다. Agent 내부 진행 이벤트 전문은 저장하지 않습니다.

## 9. 변경 규칙

입출력 필드·Tool 이름은 `docs/specs/contracts/`를 먼저 수정합니다. 이후 구현·문서를 함께 갱신합니다.

## 상세

### 4. MCP 공통 구조

Community MCP가 기준 구현입니다. 아래 경로는 `각_mcp/` 기준입니다. `server.py`에는 데이터 처리 로직을 넣지 않습니다.

| 경로 | 역할 |
| --- | --- |
| `server.py` | FastMCP 생성, Tool 등록, `/health` |
| `app/tools/` · `app/services/` · `app/clients/` | 공개 MCP Tool / 데이터 정제·계산·업무 규칙 / 외부 API·DB 연결 |
| `app/schemas/` · `app/core/` · `app/rag/` | 입력·출력 형식 / 설정·로그 / Disclosure MCP 전용 |
| `tests/` · `.env.example` · `requirements.txt` · `Dockerfile` | 테스트·환경 예제·의존성·실행 코드 완성 후 추가하는 Dockerfile |

Agent 상태·성찰은 [에이전트 아키텍처 설계서](agent-architecture.md), 실제 측정은 [시험 결과 보고서](../reports/agent-test-report.md)를 봅니다.
