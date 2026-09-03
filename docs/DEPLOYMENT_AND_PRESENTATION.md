# 로컬 분산 실행과 발표

## 1. 실행 원칙

- 개발 중에는 팀원 컴퓨터에서 서비스를 나눠 실행한다.
- 주소와 포트는 `.env`로 연결한다.
- 발표 전에는 한 컴퓨터에서도 전체 Docker 구성이 실행되게 준비한다.
- 외부 API 실패에 대비해 모든 서비스에 Mock 모드를 둔다.

## 2. 네 대의 컴퓨터 배치 예시

| 컴퓨터 | 실행 대상 |
|---|---|
| A | Frontend, Backend, PostgreSQL/pgvector, Redis |
| B | MCP Client, Price MCP |
| C | News MCP, Community MCP |
| D | Disclosure MCP |

이 배치는 담당자 이름을 확정하는 표가 아니다. 중요한 점은 일곱 서비스의 포트와 주소를 유지하는 것이다.

## 3. 고정 포트

| 서비스 | 포트 |
|---|---:|
| Backend | 8000 |
| MCP Client | 8010 |
| Price MCP | 8020 |
| News MCP | 8021 |
| Disclosure MCP | 8022 |
| Community MCP | 8023 |
| Frontend | 8501 |
| PostgreSQL | 5432 |
| Redis | 6379 |

모든 서버는 분산 실행 시 `0.0.0.0`에 바인딩한다. 다른 컴퓨터는 `localhost`가 아니라 서버 컴퓨터의 내부 IP를 사용한다.

## 4. 실행 확인 순서

1. PostgreSQL/pgvector와 Redis
2. Community MCP
3. Price·News·Disclosure MCP
4. MCP Client
5. Backend
6. Frontend
7. 삼성전자 전체 왕복
8. 미지원 기업과 일부 MCP 실패 시나리오

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
