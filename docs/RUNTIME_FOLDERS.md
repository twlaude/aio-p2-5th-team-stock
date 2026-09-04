# 실행 폴더와 담당 범위

## 1. 반드시 실행하는 서비스

완성 시 아래 일곱 서비스를 각각 독립 프로세스 또는 Docker 컨테이너로 실행한다.

| 폴더 | 포트 | 역할 |
|---|---:|---|
| `frontend/` | 8501 | 사용자 화면 |
| `backend/` | 8000 | 공개 API·로그인·성향·Memory·개인화 |
| `mcp_client/` | 8010 | 네 MCP 통합과 공통 분석 |
| `mcp_servers/price_mcp/` | 8020 | 실시간 가격 |
| `mcp_servers/news_mcp/` | 8021 | 최신 뉴스 |
| `mcp_servers/disclosure_mcp/` | 8022 | DART·기업보고서 RAG |
| `mcp_servers/community_mcp/` | 8023 | 커뮤니티 반응·공포탐욕 지수 |

## 2. 기반시설과 공통 자료

| 폴더 | 누가 관리 | 직접 서비스 실행 |
|---|---|---|
| `infra/` | Backend·AWS 또는 인프라 담당 | Docker 설정을 실행 |
| `db/` | Backend 담당, Disclosure 담당 협업 | 직접 실행하지 않음 |
| `shared/` | 모든 담당자 | 직접 실행하지 않음 |

- `infra`가 PostgreSQL/pgvector와 Redis를 시작한다.
- `db`의 Schema와 Seed를 PostgreSQL에 적용한다.
- `shared`는 공통 계약과 지원 기업 Snapshot이다.
- Frontend와 MCP Client는 DB를 직접 관리하지 않는다.

개발자는 전체 저장소를 내려받되 자신이 담당한 서비스만 실행한다. 독립 실행이란 저장소를 잘라서 배포한다는 뜻이 아니라 다른 서비스가 없어도 Mock 모드로 프로세스를 시작하고 상태를 확인할 수 있다는 뜻이다.

## 3. 실행하지 않는 영역

| 경로 | 용도 |
|---|---|
| `docs/` | 최종 설계·개발·발표 자료 |
| `docs/archive/` | 초기 검토 문서 |
| `docs/assets/` | 화면 시안과 이미지 프롬프트 |
| `archive/` | 이전 실행 코드 |
| `tests/` | 통합 검증할 때만 실행 |

루트 `README.md`와 `.gitignore`는 실행 파일은 아니지만 저장소에 유지한다.

## 4. 각 실행 서비스가 최종적으로 가져야 할 파일

```text
서비스/
├─ 실행 진입 파일
├─ app/ 또는 기능 폴더
├─ tests/
├─ .env.example
├─ requirements.txt
├─ Dockerfile
└─ GUIDE.md
```

MCP 서버의 진입점은 루트 `server.py`, Backend는 `app/main.py`, Frontend는 `app.py`로 통일한다.

## 5. 권장 관리 배치

| 담당 | 실행 폴더 |
|---|---|
| 화면 담당 | `frontend/` |
| Backend·인프라 담당 | `backend/`, `infra/`, `db/` |
| 통합 Agent 담당 | `mcp_client/` |
| 각 데이터 담당 | 맡은 `mcp_servers/*_mcp/` |

Disclosure 담당자는 DB 담당자와 pgvector 테이블만 함께 확정한다. 다른 MCP는 원본 데이터를 중앙 DB에 저장하지 않는다.

## 6. 현재 실행 가능 상태

| 서비스 | 상태 |
|---|---|
| Community MCP | 단독 실행과 테스트 가능 |
| Backend | `/health`만 가능 |
| Frontend | 최소 화면만 가능 |
| MCP Client | 아직 실행 불가 |
| Price MCP | 아직 실행 불가 |
| News MCP | 아직 실행 불가 |
| Disclosure MCP | 아직 실행 불가 |
| 전체 Docker | 아직 실행 불가 |
