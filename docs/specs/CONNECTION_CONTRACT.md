# 서비스 연결 계약

> **한눈에**
> 독립 개발 전 연결 기준입니다.
> 포트·표기·시간 제한을 맞춥니다.
> 필드는 계약부터 고친 뒤 각 서버에 반영합니다.

## 확정 연결 구조

```text
Frontend --REST/JSON--> Backend --REST/JSON--> MCP Client
                                              ├─ MCP Streamable HTTP --> Price MCP
                                              ├─ MCP Streamable HTTP --> News MCP
                                              ├─ MCP Streamable HTTP --> Disclosure MCP
                                              └─ MCP Streamable HTTP --> Community MCP
```

Frontend는 Backend만 호출합니다. Backend는 지원 기업 여부·로그인·성향·Memory(사용자 기록)·개인화를 맡습니다. MCP Client에는 사용자 정보 없이 공통 종목 분석만 요청합니다.
MCP Client는 네 MCP를 관리·호출·취합하며 외부 원본 API를 직접 호출하지 않습니다. 네 MCP는 사용자 정보·성향을 받지 않습니다.

## 확정 포트

| 서비스 | 포트 | 상태 확인 | 주요 주소 |
|---|---:|---|---|
| Frontend | 8501 | 화면 접속 | `/` |
| Backend | 8000 | `GET /health` | `/api/v1` |
| MCP Client | 8010 | `GET /health` | `/internal/v1` |
| Price MCP | 8020 | `GET /health` | `/mcp` |
| News MCP | 8021 | `GET /health` | `/mcp` |
| Disclosure MCP | 8022 | `GET /health` | `/mcp` |
| Community MCP | 8023 | `GET /health` | `/mcp` |
| PostgreSQL | 5432 | Docker 상태 확인 | DB 연결 |
| Redis | 6379 | Docker 상태 확인 | Redis 연결 |

Python 서버: `0.0.0.0` 바인딩(컨테이너·팀원 PC 접근).

## 공통 표기 규칙

- 필드명: `snake_case`. 시간: UTC ISO 8601 문자열(`2026-09-01T09:00:00Z`). Frontend에서만 Asia/Seoul로 표시합니다.
- 금액: 원 단위 정수. 비율: 퍼센트 숫자(`1.25` = `1.25%`). `request_id`·`run_id`: UUID 문자열.
- 빈 목록: `[]`. 미가용 단일 객체만 `null`. LLM(언어 모델)은 미확인 값을 추측하지 않습니다.

## 시간 제한과 반복

| 구간 | 제한 |
|---|---:|
| Frontend의 분석 요청 | 90초 |
| Backend → MCP Client | 75초 |
| MCP Client 전체 Workflow | 60초 |
| MCP Tool 1회 호출 | 15초 |
| Agent 최대 단계 | 3단계 |

재시도: 네트워크·5xx만 1회. 잘못된 요청·결과 없음·인증 실패는 제외합니다.

## 개발 순서

각 담당자가 계약의 Mock(예시 응답)을 만들고, 다른 서버 없이 실행되게 합니다.
MCP 서버 → MCP Client → Backend → Frontend 순서로 연결합니다. 계약 테스트 통과 후 실제 외부 API를 연결합니다.

## 세부 계약 문서

- `contracts/frontend_backend/README.md`: Frontend와 Backend
- `contracts/analysis/README.md`: Backend와 MCP Client
- `contracts/price/README.md`: Price MCP Tool
- `contracts/news/README.md`: News MCP Tool
- `contracts/disclosure/README.md`: Disclosure MCP Tool
- `contracts/community/README.md`: Community MCP Tool
- `contracts/user_profile/README.md`: 투자 성향
- `contracts/errors/README.md`: 상태와 오류
