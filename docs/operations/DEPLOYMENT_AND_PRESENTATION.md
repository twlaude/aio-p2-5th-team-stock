# 로컬 분산 실행과 발표

> **한눈에** — 일곱 서비스를 연결하고 발표를 준비합니다.
> 전체 왕복과 실패 상황을 먼저 확인합니다.
> 20분 발표의 중심은 `MCP → Agent → Memory`(기억) 연결입니다.

서비스는 독립 프로세스입니다. 한 컴퓨터나 여러 컴퓨터에서 `.env`로 주소·포트를 연결합니다. 실행은 [README](../../README.md#1-바로-실행-docker)를 봅니다. Backend·MCP Client·MCP 서버의 Mock(예시 응답)은 외부 API·시연 네트워크 실패 시 로컬 대체용입니다.

| 서비스 | 기본 포트·비고 |
|---|---|
| Frontend / Backend / MCP Client | 8501 (`/api`를 Backend로 프록시) / 8000 / 8010 |
| Price / News / Disclosure / Community MCP | 8020 (한국투자증권 Open API) / 8021 / 8022 / 8023 |
| PostgreSQL / Redis | 5432 / 6379 · `infra/docker-compose.yml` 기준 |

## 시연 전 확인: 8단계

**연결:** 1. PostgreSQL/pgvector(벡터 검색 확장)·Redis → 2. 네 MCP(`/health`) → 3. MCP Client(`/internal/v1/mcp-status`, 네 MCP 연결) → 4. Backend(`/health`) → 5. Frontend
**시나리오:** 6. 삼성전자 전체 왕복(비회원 → 로그인 → 회원 근거) → 7. 미지원 기업·일부 MCP 실패 → 8. 관리자 실황(`/api/v1/admin/live-status`)의 최근 요청·부분실패

## 20분 발표와 데모

| 시간 | 내용 |
|---|---|
| 2분 | 문제·목적 |
| 3분 | 전체 아키텍처·역할 분리 |
| 4분 | 네 MCP 데이터 흐름 |
| 3분 | Agent Workflow·시장 온도 |
| 2분 | 투자 성향·Memory 개인화 |
| 4분 | 실제 데모 |
| 2분 | 한계·확장 방향 |

발표는 화면 디자인보다 MCP·Agent·Memory 연결을 보여줍니다. README를 기준으로 [필수 아키텍처 설계서](../architecture/agent-architecture.md)·[시험 보고서](../reports/agent-test-report.md)를 [문서표](../../README.md#3-문서)·[팀별 작성 영역](../../README.md#5-팀별-작성-영역)에서 확인합니다.
데모는 비회원 삼성전자 검색·공개 결과 → 상세 버튼의 로그인 안내 → 서로 다른 Mock 사용자 로그인·개인화 비교 → 판단 근거·출처 → 미지원 종목 응답 순입니다. 가능하면 MCP 하나가 실패해도 부분 결과가 유지되는 장면을 보여줍니다.
