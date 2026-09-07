# 로컬 분산 실행과 발표

## 1. 실행 원칙

- 운영 기준은 VPS다. 일곱 서비스가 `systemd` 유닛으로 24시간 실행되며 `main`이 바뀌면 5분 주기 자동배포가 pull 후 바뀐 서비스만 재시작한다.
- 개발 중에는 팀원 컴퓨터에서 서비스를 나눠 실행할 수 있다. 주소와 포트는 `.env`로 연결한다.
- 외부 API 실패에 대비해 Backend·MCP Client·MCP 서버에 Mock 모드를 둔다. 발표 시연은 VPS 실서버를 쓰고, 네트워크 문제 시 로컬 Mock으로 대체한다.

## 2. 운영 배치 (VPS)

| 서비스 | 포트 | 비고 |
|---|---:|---|
| Frontend | 8501 | 발표 시연 주소, Backend 프록시 포함 |
| Backend | 8001 | 로컬 기본값은 8000 |
| MCP Client | 8010 | |
| Price MCP | 8020 | 한국투자증권 실서버 |
| News MCP | 8021 | |
| Disclosure MCP | 8022 | |
| Community MCP | 8023 | |
| PostgreSQL / Redis | 5432 / 6379 | 중앙 인스턴스 |

체크아웃·유닛 이름·확인 시각은 [실행 폴더와 운영 상태](RUNTIME_FOLDERS.md) 6절을 따른다. 로컬 분산 실행 시에도 위 포트를 유지하고, 다른 컴퓨터는 `localhost`가 아니라 서버 컴퓨터의 내부 IP를 사용한다.

## 3. 시연 전 확인 순서

1. PostgreSQL/pgvector와 Redis
2. Price·News·Disclosure·Community MCP (`/health`)
3. MCP Client (`/internal/v1/mcp-status`로 네 MCP 연결 확인)
4. Backend (`/health`)
5. Frontend
6. 삼성전자 전체 왕복 (비회원 → 로그인 → 회원 근거)
7. 미지원 기업과 일부 MCP 실패 시나리오
8. 관리자 실황 페이지(`/api/v1/admin/live-status`)에서 최근 요청·부분실패 확인

## 4. 제출 산출물

발표는 README 기반으로 진행한다. 필수 산출물 두 개는 [에이전트 아키텍처 설계서](../architecture/agent-architecture.md)와 [에이전트 시험 결과 보고서](../reports/agent-test-report.md)이며, README 5절 문서표와 6절 팀별 작성 영역에 연결되어 있다.

## 5. 20분 발표 흐름

| 시간 | 내용 |
|---:|---|
| 2분 | 문제와 서비스 목적 |
| 3분 | 전체 아키텍처와 역할 분리 |
| 4분 | 네 MCP 데이터 흐름 |
| 3분 | Agent Workflow와 시장 온도 |
| 2분 | 투자 성향과 Memory 개인화 |
| 4분 | 실제 데모 |
| 2분 | 한계와 확장 방향 |

발표의 중심은 화면 디자인보다 `MCP → Agent → Memory`가 어떻게 연결되는지 보여주는 것이다.

## 6. 데모 필수 시나리오

1. 비회원이 삼성전자를 검색해 공개 결과 확인
2. 상세 버튼에서 로그인 안내 확인
3. 서로 다른 Mock 사용자로 로그인해 개인화 결과 비교
4. 판단 근거와 출처 확인
5. 지원하지 않는 종목 응답 확인
6. 가능하면 한 MCP가 실패해도 부분 결과가 유지되는 장면 확인
