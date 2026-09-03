# 살래? 말래?

뉴스·기업보고서·커뮤니티·실시간 가격을 함께 확인하고, LLM이 근거를 종합해 현재 종목의 상황을 설명하는 교육용 주식 정보 도우미다. 매수·매도 추천이나 수익률 예측은 제공하지 않는다.

## 발표용 범위

- 기준일: 2026-09-01
- 대상: `shared/supported_companies.json`에 고정된 KOSPI 시가총액 상위 20개 보통주 기업
- 범위 밖 종목: `지원하지 않는 기업` 응답
- 뉴스·가격·커뮤니티: 실행 시점의 최신 데이터
- 기업보고서: 수집된 최신 연간 사업보고서와 최근 공시
- 사용자: 투자 성향이 미리 준비된 Mock 사용자 10명

## 확정 연결 구조

```text
Frontend --REST/JSON--> Backend --REST/JSON--> MCP Client
                                              ├─ Price MCP
                                              ├─ News MCP
                                              ├─ Disclosure MCP
                                              └─ Community MCP
```

- Frontend는 Backend만 호출한다.
- Backend는 지원 기업 확인, 로그인, 투자 성향, Memory와 개인화를 담당한다.
- MCP Client는 네 MCP를 호출하고 공통 분석을 생성한다. 외부 원본 API를 직접 호출하지 않는다.
- MCP 서버는 데이터별 Tool 제공 서버이며 사용자 정보를 받지 않는다.
- Community MCP의 실제 구조를 나머지 MCP 구현의 기준으로 사용한다.

## 사용자가 받는 결과

| 사용자 | 제공 내용 |
|---|---|
| 비회원 | 기업명, 현재 가격·등락, 공통 한 줄 설명 |
| 회원 | 비회원 결과 + 시장 온도 + 근거 요약·출처 + 투자 성향에 맞춘 확인 포인트 |

`왜 이렇게 판단했나요?`에서 회원이 아니면 `회원가입이 필요합니다!`를 표시한다.

## 개발자가 먼저 읽을 문서

1. [최종 아키텍처](docs/FINAL_ARCHITECTURE.md)
2. [서비스 연결 계약](shared/CONNECTION_CONTRACT.md)
3. [개발 실행 계획](docs/DEVELOPMENT_PLAN.md)
4. [실행 폴더와 담당 범위](docs/RUNTIME_FOLDERS.md)
5. 자신이 담당한 폴더의 `GUIDE.md`

초기 아이디어와 검토 문서는 `docs/archive/`에 보관한다. 해당 문서는 현재 개발 지시가 아니다.

## 폴더

```text
frontend/       사용자 화면
backend/        공개 API, Mock 로그인, 투자 성향, Memory, 개인화
mcp_client/     단일 Agent Workflow와 네 MCP 결과 통합
mcp_servers/    가격·뉴스·기업보고서·커뮤니티 Tool 서버
db/             PostgreSQL·pgvector 스키마와 Seed
infra/          PostgreSQL·Redis·Docker 실행 설정
shared/         팀 공통 연결·입출력 계약과 지원 기업 Snapshot
tests/          계약·통합·발표 시나리오 테스트
docs/           최종 설계·개발·발표 문서와 화면 자료
archive/        현재 실행하지 않는 이전 코드
```

## 현재 구현 상태

| 영역 | 상태 |
|---|---|
| Community MCP | Tool 2개, 외부 서버 Client, Mock, 테스트 구현 완료 |
| Backend | `/health`만 구현 |
| Frontend | 최소 Streamlit 화면만 구현 |
| MCP Client | 구조와 계약만 확정 |
| Price·News·Disclosure MCP | 구조와 계약만 확정 |
| PostgreSQL·Redis | `infra/compose.yaml`과 DB 초기화 SQL 준비 완료 |
| 서비스 Docker | Frontend·Backend·Community MCP만 준비 완료 |

## 보안 원칙

- 실제 `.env`, API Key, DB 비밀번호는 Git에 올리지 않는다.
- Frontend에는 비밀값을 넣지 않는다.
- MCP Client와 MCP 서버에는 사용자 프로필·비밀번호·토큰을 보내지 않는다.
- Memory에는 인증정보나 민감정보를 저장하지 않는다.
