# 살래? 말래? — AIO P2 5팀

> 종목을 추천하는 서비스가 아니라, 뉴스·전자공시·커뮤니티 반응을 연결해 사용자가 확인해야 할 투자 정보를 설명하는 주식 정보 도우미입니다.

## 현재 확정된 방향

- Frontend, Backend, MCP Client, MCP 서버 4개를 독립 실행 단위로 분리한다.
- MCP Client는 Price·News·Disclosure·Community MCP를 통괄하는 별도 서버로 실행한다.
- Backend는 사용자 투자 성향과 Memory를 관리하고, 분석에 필요한 성향 네 값만 MCP Client에 전달한다.
- MCP Client는 공통 분석과 회원별 확인 포인트를 생성한다.
- 뉴스·공시·커뮤니티 MCP는 Agent가 아니라 Tool 제공 서버다.
- MCP Client 안에는 하나의 Stock Analysis Agent와 이를 통제하는 Workflow를 둔다.
- 각 서비스는 독립 Docker 컨테이너로 실행할 수 있게 준비한다.
- 개발 중에는 팀원 컴퓨터에 분산하고, 발표 때는 한 컴퓨터에서도 전체 실행할 수 있게 한다.

## 전체 연결 구조

```text
Frontend
  ↓ HTTP
Backend
  ├─ 로그인·사용자 구분
  ├─ 투자 성향·Memory
  └─ 지원 종목 확인·성향 전달
       ↓ HTTP
MCP Client 통합 서버
  ├─ 결정적 Workflow
  ├─ Single Stock Analysis Agent
  ├─ 공통 분석·개인화 확인 포인트
  └─ MCP Tool Client
       ↓ Streamable HTTP
  ┌──────┼───────────┬─────────────┐
Price MCP News MCP Disclosure MCP Community MCP
       ↓
PostgreSQL + pgvector / Redis / 외부 데이터
```

## 주요 문서

1. `guide/06_CONFIRMED_LOCAL_STRUCTURE.md`: 확정된 전체 구조
2. `guide/07_AGENT_WORKFLOW_GUIDE.md`: 수업 내용을 적용한 Agent Workflow
3. `발표.md`: 컴퓨터 분산 실행과 발표 구성
4. `plan.md`: 단계별 개발 계획
5. 각 최상위 폴더의 `GUIDE.md`: 영역별 책임과 구현 기준
6. `실행_폴더_구분.md`: 실제 구동 폴더와 참고용 폴더 구분
7. `shared/CONNECTION_CONTRACT.md`: 확정 포트·Endpoint·Tool·공통 규칙

## 폴더

```text
frontend/       사용자 화면
backend/        인증·Memory·투자 성향 조회·Frontend API
mcp_client/     Agent Workflow와 MCP 결과 통합 서버
mcp_servers/    주가·뉴스·전자공시·커뮤니티 Tool 서버
db/             PostgreSQL·pgvector 구조
shared/         서비스 간 공통 입출력 계약
infra/          PostgreSQL·Redis와 Docker 실행 설정 영역
tests/          계약·통합·시나리오 테스트 영역
legacy/         이전 단일 MCP 골격 보존
guide/           설계 문서
text/           화면 이미지 프롬프트와 결과
```

## 현재 상태

Backend, News MCP, Community MCP는 기본 실행 코드가 반영되어 있다. MCP Client, Price MCP, Disclosure MCP와 React Frontend는 담당자가 계약에 맞춰 구현하는 단계다. 기존 단일 MCP 코드는 `legacy/stock_mcp`에 참고용으로 보존한다.

## 확정 역할

| 팀원 | 담당 |
|---|---|
| 오현님 | 전체 방향·통합 관리, MCP Client/Agent 전체, Price MCP 전체, 발표 |
| 태웅님 | React Frontend 전체, Community MCP와 커뮤니티 원본 서버 전체 |
| 기화님 | Backend 전체, News MCP 전체 |
| 인혜님 | Disclosure MCP 전체, DART 연동, 기업보고서 처리, RAG·임베딩·벡터 검색 |

## 보안 원칙

- 실제 `.env`와 API Key는 Git에 올리지 않는다.
- Frontend에는 비밀값을 넣지 않는다.
- 사용자 ID는 실제 단계에서 인증된 토큰으로 확인한다.
- Memory에는 비밀번호, 토큰, API Key, 주민등록번호 같은 민감정보를 저장하지 않는다.
- 서비스는 매수·매도 추천이나 수익률 보장을 제공하지 않는다.
