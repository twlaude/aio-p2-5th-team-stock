# 확정된 로컬 개발 구조

> 상태: 팀에서 확정한 방향을 반영한 구조 가이드
> 범위: 폴더와 역할 설명만 다루며, 구현 코드는 포함하지 않는다.

## 1. 프로젝트 한 문장 정의

사용자가 종목을 검색하면 뉴스, 전자공시, 커뮤니티 반응을 한곳에 모아 공통 분석을 제공하고, 사용자의 투자 성향과 관련된 Memory만 사용해 개인별 확인 포인트를 보여주는 정보 도우미를 만든다.

이 서비스는 종목 추천, 매수·매도 판단, 목표가격 예측을 제공하지 않는다.

## 2. 확정된 실행 단위

각 구성요소는 로컬에서 독립적으로 실행한다.

```text
Frontend
  ↓ HTTP
Backend
  ├─ 로그인·사용자 구분
  ├─ 투자 성향·Memory
  └─ 개인화 결과 조립
       ↓ HTTP
MCP Client 통합 서버
  ├─ 결정적 Workflow
  ├─ Single Stock Analysis Agent
  └─ Agent Runtime·Trace
       ↓ MCP
  ┌────┼────────┬────────┐
주가  뉴스  전자공시  커뮤니티 MCP 서버
       ↓
PostgreSQL / pgvector / Redis
```

`MCP Client`는 Backend 내부 모듈이 아니라 독립적인 통합 서버로 운영한다.

## 3. 목표 폴더 구조

```text
aio-p2-5th-team-stock/
├─ frontend/                    # 사용자 화면
├─ backend/                     # 인증, Memory, 개인화, Frontend API
├─ mcp_client/                  # MCP 호출과 공통 종목 분석을 통괄하는 서버
│  └─ app/
│     ├─ workflows/             # 전체 순서와 통제 지점
│     ├─ agents/                # Agent Goal·Instructions·Tool 권한
│     ├─ runtime/               # Tool Result 재판단 Loop와 종료
│     └─ clients/               # 네 MCP 서버 연결
├─ mcp_servers/
│  ├─ price_mcp/                # 현재가·등락·가격 활동도
│  ├─ news_mcp/                 # 실시간 뉴스
│  ├─ disclosure_mcp/           # DART·기업보고서·RAG
│  └─ community_mcp/            # 커뮤니티 데이터
├─ db/                          # PostgreSQL·pgvector 데이터 구조
├─ shared/                      # 서비스 간 공통 입출력 계약
├─ infra/                       # PostgreSQL·Redis 로컬 실행 설정
├─ tests/                       # 전체 연결 테스트 계획
├─ legacy/                      # 이전 단일 MCP 골격 보존
├─ gide/                        # 프로젝트 설계 문서
└─ text/                        # 화면 이미지 생성 프롬프트와 결과
```

## 4. 폴더별 가이드 위치

| 영역 | 읽을 문서 |
|---|---|
| Frontend | `frontend/GUIDE.md` |
| Backend | `backend/GUIDE.md` |
| 로그인·Mock 사용자 | `backend/AUTH_GUIDE.md` |
| Memory | `backend/MEMORY_GUIDE.md` |
| MCP Client | `mcp_client/GUIDE.md` |
| Agent Workflow | `gide/07_AGENT_WORKFLOW_GUIDE.md` |
| MCP 서버 전체 | `mcp_servers/GUIDE.md` |
| 주가 MCP | `mcp_servers/price_mcp/GUIDE.md` |
| 뉴스 MCP | `mcp_servers/news_mcp/GUIDE.md` |
| 전자공시 MCP | `mcp_servers/disclosure_mcp/GUIDE.md` |
| 커뮤니티 MCP | `mcp_servers/community_mcp/GUIDE.md` |
| Database | `db/GUIDE.md` |
| 공통 계약 | `shared/GUIDE.md` |
| 로컬 인프라 | `infra/GUIDE.md` |
| 전체 연결 테스트 | `tests/GUIDE.md` |

## 5. 가장 중요한 책임 구분

### Frontend

- Backend만 호출한다.
- DB, Redis, 외부 API, MCP 서버를 직접 호출하지 않는다.
- FE0 로그인·투자 성향, FE1 검색, FE2 분석 결과를 보여준다.

### Backend

- 현재 사용자를 구분한다.
- 투자 성향과 Memory를 관리한다.
- MCP Client에 종목 분석을 요청한다.
- 공통 분석에 사용자별 확인 포인트를 추가한다.

### MCP Client

- 주가·뉴스·전자공시·커뮤니티 MCP 서버를 통괄한다.
- 네 서버의 결과를 공통 규격으로 정리한다.
- 외부 원본 API를 직접 호출하지 않는다.
- 사용자 개인정보 없이 공통 종목 분석을 만든다.
- 안전한 전체 순서는 Workflow가 통제한다.
- 하나의 Stock Analysis Agent가 Goal과 State를 보고 추가 Tool 또는 종료를 판단한다.
- Tool Allowlist, arguments 검증, 최대 단계, 종료 이유와 Trace를 관리한다.

### MCP 서버

- 자신이 담당한 데이터만 수집·검색·정제한다.
- 확인하지 못한 내용을 추측하지 않는다.
- 출처, 수집 시각, 조회 상태를 함께 반환한다.

### Database와 Redis

- PostgreSQL: 회원, 투자 성향, 장기 Memory, 대화 기록
- pgvector: 공시·보고서 등 긴 문서의 검색용 청크
- Redis: 현재 종목, 진행 단계, 최근 대화 등 단기 상태

## 6. 로그인과 Mock Data의 관계

Mock Data를 사용해도 사용자를 구분하는 기능은 필요하다.

첫 단계에서는 실제 회원가입 대신 데모 사용자를 선택한다.

```text
데모 사용자 A: 안정형·장기·초보
데모 사용자 B: 공격형·단기·경험 있음
```

Backend는 `X-Demo-User-ID`와 같은 교육용 식별 방식으로 사용자를 구분할 수 있다. 실제 로그인 단계에서는 인증된 토큰의 사용자 ID로 교체한다. Frontend가 요청 본문에 임의의 사용자 ID를 넣어 권한을 결정하게 만들면 안 된다.

## 7. Memory와 종목 데이터의 경계

```text
사용자 Memory
├─ 투자 성향
├─ 투자 기간
├─ 투자 경험
└─ 선호하는 근거

종목 분석 데이터
├─ 주가
├─ 뉴스
├─ 전자공시
├─ 기업보고서
└─ 커뮤니티 반응
```

공통 종목 분석은 사용자마다 달라지지 않는다. Backend가 공통 분석을 받은 뒤 관련 Memory만 선택하여 `나를 위한 확인 포인트`를 별도로 만든다.

## 8. 구현 순서

1. 서비스 간 입력·출력 규격 확정
2. Mock 사용자와 Mock 투자 성향 준비
3. Mock MCP 응답으로 Frontend → Backend → MCP Client 왕복 확인
4. 주가·뉴스·전자공시·커뮤니티 MCP를 하나씩 연결
5. PostgreSQL 장기 Memory 연결
6. Redis 단기 상태 연결
7. 실제 로그인으로 교체
8. 관리자 페이지와 추가 기능 검토

## 9. 기존 폴더에 대한 처리

이전 `mcp_server/stock_mcp` 골격은 삭제하지 않고 `legacy/stock_mcp`로 이동해 보존했다.

새 방향은 `mcp_servers/price_mcp`, `mcp_servers/news_mcp`, `mcp_servers/disclosure_mcp`, `mcp_servers/community_mcp`로 분리하는 것이다. 실제 구현을 시작할 때 Legacy 골격에서 재사용할 부분만 새 서버로 옮긴다.

## 10. 현재 문서의 의미

기존 `gide/00`부터 `gide/05`까지는 아이디어를 정리하던 시점의 초안이다. 폴더 분리와 MCP 연결 구조가 충돌할 경우 이 문서와 각 폴더의 `GUIDE.md`를 최신 기준으로 사용한다.
