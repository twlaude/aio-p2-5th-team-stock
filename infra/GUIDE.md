# 로컬 실행 환경 가이드

## 목적

팀원들이 각자 맡은 서버를 로컬에서 실행하고 환경변수의 주소만 바꿔 서로 연결할 수 있도록 실행 환경을 관리한다.

## 로컬 실행 대상

```text
Frontend
Backend
MCP Client
Price MCP
News MCP
Disclosure MCP
Community MCP
PostgreSQL + pgvector
Redis
```

## 확정 포트

아래 값을 팀 공통 기본값으로 사용한다.

| 구성요소 | 포트 예시 |
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

## `.env` 원칙

- 각 실행 폴더는 자기 `.env.example`을 가진다.
- 실제 `.env`는 Git에 올리지 않는다.
- API Key와 비밀번호는 문서에 실제 값으로 적지 않는다.
- Frontend에는 Backend 주소 외의 비밀값을 넣지 않는다.

## 의존성 원칙

- Python 서버마다 별도의 `requirements.txt`를 사용한다.
- 팀원이 맡지 않은 서버의 패키지까지 한꺼번에 설치하지 않는다.
- 공통 버전이 필요한 핵심 패키지는 문서로 맞춘다.

## Docker 적용 범위

초기에는 PostgreSQL, pgvector, Redis만 Docker로 실행하는 방향이 단순하다. 각 Python 서버는 팀원 컴퓨터에서 직접 실행할 수 있다.

## 연결 점검 순서

1. PostgreSQL과 Redis 실행
2. 각 MCP 서버 단독 실행
3. MCP Client에서 네 MCP 연결 확인
4. Backend에서 MCP Client 연결 확인
5. Frontend에서 Backend 연결 확인

한 번에 전체를 실행하기보다 아래에서 위 순서로 연결을 확인한다.
