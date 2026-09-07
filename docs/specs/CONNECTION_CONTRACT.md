# 서비스 연결 계약

이 문서는 팀원들이 각 서버를 독립적으로 개발하기 전에 공통으로 지켜야 하는 연결 기준이다. 구현 중 필드가 필요해지면 이 문서를 먼저 수정한 뒤 각 서버에 반영한다.

## 확정 연결 구조

```text
Frontend --REST/JSON--> Backend --REST/JSON--> MCP Client
                                              ├─ MCP Streamable HTTP --> Price MCP
                                              ├─ MCP Streamable HTTP --> News MCP
                                              ├─ MCP Streamable HTTP --> Disclosure MCP
                                              └─ MCP Streamable HTTP --> Community MCP
```

- Frontend는 Backend만 호출한다.
- Backend는 지원 기업 여부, 로그인, 투자 성향, Memory와 개인화를 담당한다.
- Backend는 사용자 정보 없이 MCP Client에 공통 종목 분석만 요청한다.
- MCP Client는 네 MCP 서버를 관리·호출·취합하며 외부 원본 API는 직접 호출하지 않는다.
- 네 MCP 서버는 사용자 정보와 투자 성향을 받지 않는다.

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

모든 Python 서버는 컨테이너와 다른 팀원 PC에서 접근할 수 있도록 `0.0.0.0`에 바인딩한다.

## 공통 표기 규칙

- JSON 필드명은 `snake_case`를 사용한다.
- 시간은 UTC ISO 8601 문자열을 사용한다. 예: `2026-09-01T09:00:00Z`.
- Frontend에서만 Asia/Seoul 시간으로 변환해 표시한다.
- 금액은 원 단위 정수, 비율은 퍼센트 숫자를 사용한다. 예: `1.25`는 `1.25%`다.
- `request_id`와 `run_id`는 UUID 문자열을 사용한다.
- 목록 결과가 없으면 `null` 대신 빈 배열 `[]`을 사용한다.
- 사용할 수 없는 단일 객체만 `null`로 표시한다.
- 확인하지 못한 값은 LLM이 추측하여 채우지 않는다.

## 시간 제한과 반복

| 구간 | 제한 |
|---|---:|
| Frontend의 분석 요청 | 90초 |
| Backend → MCP Client | 75초 |
| MCP Client 전체 Workflow | 60초 |
| MCP Tool 1회 호출 | 15초 |
| Agent 최대 단계 | 3단계 |

네트워크 오류와 5xx 오류만 한 번 재시도한다. 잘못된 요청, 결과 없음, 인증 실패는 재시도하지 않는다.

## 개발 순서

1. 각 담당자는 자기 계약의 Mock 응답부터 만든다.
2. 각 서버는 다른 서버가 없어도 Mock 모드에서 실행 가능하게 한다.
3. MCP 서버 → MCP Client → Backend → Frontend 순서로 연결한다.
4. 계약 테스트가 통과한 뒤 실제 외부 API를 연결한다.

## 세부 계약 문서

- `contracts/frontend_backend/README.md`: Frontend와 Backend
- `contracts/analysis/README.md`: Backend와 MCP Client
- `contracts/price/README.md`: Price MCP Tool
- `contracts/news/README.md`: News MCP Tool
- `contracts/disclosure/README.md`: Disclosure MCP Tool
- `contracts/community/README.md`: Community MCP Tool
- `contracts/user_profile/README.md`: 투자 성향
- `contracts/errors/README.md`: 상태와 오류
