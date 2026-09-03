# 프로젝트 실행 계획

## 1. 현재 상태

- 서비스 아이디어와 FE0·FE1·FE2 흐름을 정리했다.
- Frontend, Backend, MCP Client, MCP 서버 4개의 책임을 분리했다.
- Memory 수업 내용을 투자 성향과 단기 상태에 연결했다.
- Agent Workflow 수업 내용을 MCP Client 구조에 반영했다.
- 각 실행 영역의 폴더와 가이드 문서를 만들었다.
- 기존 단일 MCP 골격은 `legacy/stock_mcp`에 보존했다.

현재 `main`에 구현된 내용:

- Backend의 인증·프로필·분석·Memory 기본 코드
- News MCP 실행 코드와 테스트
- Community MCP 실행 코드와 테스트

아직 구현하거나 통합해야 하는 내용:

- MCP Client 실행 코드
- Price MCP 실행 코드
- Disclosure MCP와 기업보고서 RAG 실행 코드
- React Frontend 화면과 Backend 연결
- Dockerfile과 통합 Docker Compose
- 실제 PostgreSQL·Redis 연결
- 실제 주가·DART 연결과 전체 서비스 통합
- 실제 Agent Runtime과 OpenAI 연결

## 2. 확정된 기술 방향

```text
Frontend → Backend → MCP Client → 네 MCP 서버
              │             │
       PostgreSQL·Redis   Single Agent Workflow
```

- Frontend는 Backend만 호출한다.
- Backend는 인증, Memory와 투자 성향 조회를 담당하고 성향 네 값만 MCP Client에 전달한다.
- MCP Client는 독립 통합 서버다.
- MCP Client는 공통 분석과 회원별 확인 포인트 생성을 담당한다.
- MCP 서버는 Agent가 아니라 Tool 제공 서버다.
- 초기에는 하나의 Stock Analysis Agent만 사용한다.
- 전체 안전 순서는 결정적 Workflow가 통제한다.
- LLM은 필요한 추가 Tool과 종료를 판단한다.
- 모든 Tool Call은 Allowlist와 arguments 검증 후 실행한다.

## 3. 1단계: 공통 계약 확정

### 목표

팀원이 서로 다른 서버를 만들어도 연결 가능한 입력·출력 규격을 정한다.

### 작업

- `user_profile` 계약
- `analysis_request` 계약
- 뉴스 MCP 응답 계약
- 전자공시 MCP 응답 계약
- 커뮤니티 MCP 응답 계약
- 최종 `common_analysis` 계약
- `personalized_checkpoints` 계약
- 오류와 부분 성공 계약
- 날짜·시간 형식 통일

### 완료 기준

삼성전자 Mock Data가 모든 계약을 만족하고, 각 팀원이 같은 JSON 예시를 이해한다.

## 4. 2단계: 독립 실행 골격과 Docker

### 목표

각 폴더만 받은 팀원이 자신의 서비스를 독립 실행한다.

### 작업

- 각 서비스 `Dockerfile`
- 각 서비스 `.env.example`
- 각 서비스 `requirements.txt`
- 각 서비스 상태 확인 API
- Mock 모드
- 포트 확정
- PostgreSQL·Redis Docker Compose

### 완료 기준

각 서비스가 다른 서비스 없이도 컨테이너를 시작하고, Mock 상태 확인 결과를 반환한다.

## 5. 3단계: Mock 전체 연결

### 목표

실제 외부 API 없이 전체 왕복을 확인한다.

```text
Frontend
→ Backend
→ MCP Client
→ Mock Price·News·Disclosure·Community MCP
→ MCP Client
→ Backend
→ Frontend
```

### 완료 기준

삼성전자 검색 후 공통 분석과 개인화 확인 포인트가 FE2에 표시된다.

## 6. 4단계: 로그인과 Memory

### 첫 구현

- 데모 사용자 A·B
- 교육용 사용자 식별 헤더
- Mock 투자 성향
- 투자 성향이 없을 때 FE0 이동
- 보류된 검색 종목 복원

### 다음 구현

- PostgreSQL 장기 Memory
- Redis 단기 State와 TTL
- 최근 대화 일부
- 사용자 Memory 조회·수정·삭제
- 실제 로그인과 인증 토큰

### 완료 기준

같은 삼성전자를 검색했을 때 공통 분석은 같고 사용자 A·B의 개인화 확인 포인트만 다르다.

## 7. 5단계: 실제 MCP 데이터

### Price MCP

- 공공데이터포털 금융위원회 주식시세정보 API
- 현재가·대비·등락률과 기준 시각
- 지원 기업 20개의 가격 활동도 Snapshot
- 종목별 1분 캐시

### News MCP

- 뉴스 API 선택
- 검색·중복 제거
- 발행 시각과 출처 URL
- 결과 없음과 API 실패 구분

### Disclosure MCP

- DART 기업번호
- 공시 목록과 원문
- 기업보고서 청킹·임베딩
- 종목·문서 종류 선필터 후 벡터 검색

### Community MCP

- 태웅님 원본 서버 연결
- 표본 수와 분석 기간
- 긍정·중립·부정 반응
- 주요 주제

### 완료 기준

각 MCP가 자기 데이터만 책임지고, 공통 계약과 출처 규칙을 지킨다.

## 8. 6단계: Agent Workflow

### Workflow가 통제할 단계

```text
요청 검증
→ 회사 확인
→ 필수 데이터 수집
→ Agent 실행
→ 근거 검증
→ 결과 형식 검증
→ Backend 반환
```

### Agent가 판단할 단계

- 어떤 추가 Tool이 필요한가
- Tool Result가 충분한가
- 서로 충돌하는 근거를 어떻게 설명할 것인가
- 추가 조회할 것인가 또는 종료할 것인가

### Agent State

```text
run_id
goal
question
company
status
step
tool_results
llm_calls
tool_calls
answer
termination_reason
trace
```

### 종료 이유

```text
completed
no_data
partial_completed
model_error
invalid_tool_call
mcp_tool_error
max_steps_exceeded
workflow_timeout
```

### 완료 기준

Tool Result가 Model에 다시 전달되고, Agent가 추가 Tool 또는 최종 답변을 선택한다. 최대 반복 수와 구조화된 종료 이유가 남는다.

## 9. 7단계: 분산 통합과 발표 준비

- 팀원 컴퓨터 4대 분산 실행
- 내부 IP와 포트 연결
- Windows 방화벽 확인
- MCP Streamable HTTP 확인
- 일부 서버 실패 시 부분 성공 확인
- 발표용 한 컴퓨터 통합 Docker Compose
- 실제 API 실패용 Mock 모드
- 20분 발표 순서와 데모 리허설

## 10. 확정 역할 분담

다음 표를 현재 개발 담당 기준으로 사용한다.

| 팀원 | 우선 영역 | 함께 확인할 영역 |
|---|---|---|
| 오현님 | MCP Client/Agent 전체, Price MCP 전체 | 전체 제품 방향, 통합 계약·테스트, 발표 |
| 태웅님 | React Frontend 전체, Community MCP와 원본 서버 전체 | 화면 흐름, 커뮤니티 계약과 표본 규칙 |
| 기화님 | Backend 전체, News MCP 전체 | 인증·Memory·투자 성향 전달, 뉴스 계약 |
| 인혜님 | Disclosure MCP 전체 | DART, 기업보고서 처리, RAG·임베딩·pgvector |

## 11. 첫 구현 전 결정 결과

1. Frontend: React 기반으로 구현
2. 포트: React Frontend 포트는 Frontend 설정에서 확정하고, Backend 8000, MCP Client 8010, MCP 서버 8020~8023을 사용
3. 전송: Frontend·Backend·MCP Client는 REST/JSON, MCP 서버는 Streamable HTTP `/mcp`
4. 요청·응답: `shared/CONNECTION_CONTRACT.md`와 하위 계약으로 확정
5. 뉴스: NAVER API HUB 뉴스 검색 API
6. DART: 최신 연간 사업보고서 저장·임베딩, 최근 30일 공시 목록과 상세 1~2건
7. 커뮤니티: 최근 7일 최대 100건을 집계하고 표본 상태를 함께 반환
8. LLM: 공통 분석과 개인화 모두 OpenAI `gpt-5.6-luna`
9. Agent 최대 단계: 3
10. 발표 종목: 2026년 9월 1일 기준 KOSPI 시가총액 상위 20개 보통주 기업

20개 기업명과 종목 코드는 2026-09-02에 `shared/supported_companies.json`으로 확정했으며 종목 코드와 순위를 포함한다.

## 12. 이번 프로젝트에서 보류할 항목

- 여러 LLM Agent를 사용하는 Multi-Agent Orchestration
- 자동 매수·매도 판단
- 목표주가와 미래 수익률 예측
- 복잡한 관리자 페이지
- 종목별 사용자 커뮤니티
- 결제나 실제 주문처럼 상태를 변경하는 Tool

네 MCP 서버가 있다고 해서 Multi-Agent는 아니다. 초기에는 하나의 Goal과 State를 가진 Single Stock Analysis Agent로 충분하다. 독립 Goal과 Tool 권한이 실제로 나뉠 필요가 확인된 뒤에만 Multi-Agent를 검토한다.
