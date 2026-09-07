# 실행 폴더와 담당 범위

## 1. 반드시 실행하는 서비스

아래 일곱 서비스가 구현되어 있습니다. 표의 포트는 로컬 기본값이며, 6절의 VPS 운영 값과 구분합니다.

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
| `docs/archive/design-drafts/` | 초기 화면 시안(구현 완료 후 보관) |
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

MCP 서버와 MCP Client의 진입점은 각 폴더의 `server.py`, Backend는 `app/main.py`, Frontend는 Vite의 `index.html`·`src/main.tsx`입니다. Frontend는 Python `app.py`를 실행하지 않습니다.

## 5. 권장 관리 배치

| 담당 | 실행 폴더 |
|---|---|
| 화면 담당 | `frontend/` |
| Backend·인프라 담당 | `backend/`, `infra/`, `db/` |
| 통합 Agent 담당 | `mcp_client/` |
| 각 데이터 담당 | 맡은 `mcp_servers/*_mcp/` |

Disclosure 담당자는 DB 담당자와 pgvector 테이블만 함께 확정한다. 다른 MCP는 원본 데이터를 중앙 DB에 저장하지 않는다.

## 6. VPS 운영 상태와 로컬 개발 구분

2026-09-07 13:33:40 KST에 systemd의 ActiveState/SubState, WorkingDirectory와 실제 LISTEN 포트를 읽기 전용으로 확인했습니다. 아래 일곱 unit은 모두 `active/running`이었습니다. 작업용 worktree와 운영 체크아웃 `/root/team5_deploy`는 별개입니다.

| systemd unit | 운영 체크아웃 아래 WorkingDirectory | 실제 포트 |
|---|---|---:|
| `com.twmoon.team5-backend.service` | `backend` | 8001 |
| `com.twmoon.team5-mcp-client.service` | `mcp_client` | 8010 |
| `com.twmoon.team5-price-mcp.service` | `mcp_servers/price_mcp` | 8020 |
| `com.twmoon.team5-news-mcp.service` | `mcp_servers/news_mcp` | 8021 |
| `com.twmoon.team5-disclosure-mcp.service` | `mcp_servers/disclosure_mcp` | 8022 |
| `com.twmoon.team5-community-mcp.service` | `mcp_servers/community_mcp` | 8023 |
| `com.twmoon.team5-frontend.service` | `frontend` | 8501 |

운영 체크아웃은 `/srv/team5/deploy`(main 자동 pull), 실행 계정은 `team5`, Python 가상환경은 `/srv/team5/venvs/<서비스>`, 서비스 로그는 `/srv/team5/logs/<유닛>.log`입니다 (2026-09-07 기준).

Backend의 로컬 기본은 8000이지만 팀 VPS 운영 포트는 8001입니다. 관측 당시 8000은 `/root/stock_insight_solo/backend`의 별도 서비스였습니다. 로컬 명령의 포트를 운영 포트로 간주하지 않습니다.

운영 체크아웃 HEAD는 `e6d611c858caa16ea4059148a4f4ef1fa5b1dfdd`였습니다. 성찰 구현 `94ee2d7`과 v2 검증기 `52eff44`는 해당 HEAD의 조상이 아니며, 배포 파일에 성찰 설정·`reflection_calls`·`runtime/verifier.py`도 없었습니다. 이 확인은 체크아웃 상태이며 프로세스가 모든 최신 파일을 재로딩했다는 증거까지 뜻하지 않습니다. [시험 보고서](agent-test-report.md)의 성찰 비교는 작업 브랜치 기준입니다.

현재 Backend에는 인증·회원가입·성향·Memory·분석·관리자 실황이, Frontend에는 React 분석 화면이 구현되어 있습니다. MCP Client와 네 MCP도 실제 연동 코드가 있으며 이번 캡처·기존 시험의 범위는 [설계서](agent-architecture.md)와 [시험 보고서](agent-test-report.md)에 기록합니다. 저장소 Dockerfile은 6개이며 Disclosure에는 없어 전체 Docker 배포 완료로 표시하지 않습니다.

이 관측에서는 서비스 시작·재시작·중단·배포·환경 변경을 수행하지 않았습니다. 로컬 실행은 [체크리스트](LOCAL_RUN_ENV_CHECKLIST.md)를 따릅니다.
