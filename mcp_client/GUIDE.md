# MCP Client 통합 서버 가이드

## 확정된 역할

MCP Client는 Backend와 분리된 독립 서버다. 내부에서는 Price·News·Disclosure·Community 네 MCP 서버의 Client로 동작하고, 외부에서는 Backend가 호출하는 통합 API 서버로 동작한다.

하나의 Stock Analysis Agent, 이를 실행하는 Runtime, 전체 안전 순서를 통제하는 Workflow를 포함한다.

MCP Client는 관리자이자 연결 통로다. 공공데이터·NAVER·DART·커뮤니티 원본 API를 직접 호출하지 않고 반드시 담당 MCP Tool을 통해 데이터를 받는다.

## 목표 구조

```text
mcp_client/
├─ app/
│  ├─ api/                  # Backend가 호출하는 HTTP API
│  ├─ workflows/            # 입력 검증·필수 조회·검증·반환 순서
│  ├─ agents/               # Goal·Instructions·Allowed Tools
│  ├─ runtime/              # Agent Loop·State·종료·Trace
│  ├─ clients/              # 네 MCP 서버의 Streamable HTTP Client
│  │  ├─ price/
│  │  ├─ news/
│  │  ├─ disclosure/
│  │  └─ community/
│  ├─ services/
│  │  ├─ company_resolver/
│  │  ├─ data_collector/
│  │  └─ analysis_builder/
│  ├─ providers/            # LLM Provider
│  ├─ schemas/              # 요청·응답·State 규격
│  ├─ prompts/              # 공통 분석 지침
│  ├─ core/                 # 설정·로그·타임아웃
│  └─ main.py
├─ tests/
├─ .env.example
├─ requirements.txt
└─ GUIDE.md
```

## Workflow와 Agent

### Workflow가 담당

```text
Backend 요청 검증
→ 회사명·종목 코드 확인
→ 네 MCP의 기본 Tool 병렬 호출
→ 기본 결과를 Agent State에 입력
→ Agent Runtime 실행
→ 출처·응답 Schema 검증
→ Backend 반환
```

### Agent가 담당

- 기본 결과가 충분한지 판단
- 필요한 상세 Tool 선택
- Tool Result를 보고 추가 조회 또는 종료 선택
- 근거의 일치·충돌 설명
- 추천 없이 공통 분석 작성
- Backend가 투자 성향을 전달한 회원 요청에만 개인화 확인 포인트 작성

MCP 서버가 네 개여도 Agent는 하나다. 각 MCP는 Tool 제공 서버이며 독립적인 판단 주체가 아니다.

## Agent Runtime 필수 기능

- Tool discovery
- Agent별 Tool Allowlist
- arguments JSON Object 검증
- MCP Tool 실행
- Tool Result를 Model에 재전달
- 최대 반복 단계
- 구조화된 `termination_reason`
- Model·Tool 호출 Trace
- 오류 정보에서 비밀값 제거

## 확정 입출력 계약

Backend 연결 주소와 전체 JSON은 `shared/contracts/analysis/README.md`를 따른다.

입력 핵심 필드:

```text
request_id
company.company_name
company.stock_code
investment_profile 또는 null
requested_at
```

출력 핵심 필드:

```text
run_id
status
termination_reason
company
collected_at
market_temperature
evidence_level
one_line_summary
news_summary
disclosure_summary
community_summary
personalized_checkpoints 또는 null
evidence
sources
partial_failures
trace_summary
```

필드 이름과 자료형을 임의로 바꾸지 않는다. 변경이 필요하면 `shared` 계약을 먼저 수정한다.

## 일부 서버 실패

```text
가격: 성공
뉴스: 성공
전자공시: 성공
커뮤니티: 실패
```

이 경우 확인된 뉴스와 공시는 유지하되 `partial_completed`와 제한사항을 반환한다. 실패한 데이터를 Model이 추측으로 채우게 하지 않는다.

## 환경변수 계획

```text
MCP_CLIENT_HOST=0.0.0.0
MCP_CLIENT_PORT=8010

PRICE_MCP_URL=http://localhost:8020/mcp
NEWS_MCP_URL=http://localhost:8021/mcp
DISCLOSURE_MCP_URL=http://localhost:8022/mcp
COMMUNITY_MCP_URL=http://localhost:8023/mcp
MCP_REQUEST_TIMEOUT_SECONDS=15

LLM_PROVIDER
OPENAI_API_KEY
OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=low
MAX_AGENT_STEPS=3
WORKFLOW_TIMEOUT_SECONDS=60
```

## 확정 LLM과 토큰 절감 규칙

공통 종목 분석은 OpenAI의 `gpt-5.6-luna`를 사용한다. 발표용 MVP는 구현 확인이 목적이므로 처음부터 더 비싼 모델을 섞지 않고 Luna 하나로 통일한다.

담당자는 다음 규칙을 지킨다.

1. 뉴스는 중복을 제거한 뒤 핵심 기사 최대 5건만 LLM에 전달한다.
2. 기업보고서는 MCP Client가 정한 분석 주제와 관련된 검색 결과 3~5개 조각만 전달하고 보고서 전체를 넣지 않는다.
3. 커뮤니티 게시글 원문 최대 100개를 그대로 전달하지 않는다. Community MCP가 만든 반응 비율, 주요 기대·우려 주제, 대표 근거만 전달한다.
4. 매 호출마다 네 MCP의 원본 응답 전체를 넣지 않고 공통 Schema에 맞게 필요한 필드만 추린다.
5. LLM 출력은 자유로운 장문이 아니라 정해진 JSON Schema와 짧은 길이 제한을 사용한다.
6. 동일 종목의 공통 분석은 데이터 기준 시각과 함께 캐시하여 같은 자료로 반복 생성하지 않는다.
7. Agent 반복 횟수는 `MAX_AGENT_STEPS=3`으로 제한한다.
8. 요청별 입력·출력·추론 토큰 사용량을 기록하여 발표 준비 중 비정상적으로 큰 호출을 찾는다.
9. 출처가 부족한 경우 추가 호출을 무한 반복하지 않고 `insufficient_evidence` 또는 부분 완료 상태로 종료한다.

OpenAI API Key는 `.env`에만 저장하고 Git에 올리지 않는다. `.env.example`에는 변수 이름과 모델명 예시만 둔다.

## 하지 않는 일

- 회원가입과 로그인
- 사용자 장기 Memory 저장
- 사용자별 투자 성향 저장·조회·수정
- 공공데이터·NAVER·DART·커뮤니티 원본 API 직접 호출
- 주가·뉴스·공시·커뮤니티 원본 저장
- 사용자에게 직접 매수·매도 추천
- 네 MCP 서버를 서로 다른 Agent라고 부르기

## 완료 기준

1. Backend와 별도 컨테이너로 실행된다.
2. 네 MCP 서버의 Tool을 발견하고 호출한다.
3. 필수 기본 조회는 Workflow가 통제한다.
4. Tool Result를 본 Agent가 추가 Tool 또는 종료를 판단한다.
5. 최대 단계와 종료 이유가 남는다.
6. 출처와 수집 시각을 유지한다.
7. 일부 MCP 실패를 구조화해서 반환한다.
8. 회원 요청에는 투자 성향 네 값만 사용해 `personalized_checkpoints`를 만들고, 비회원 요청에는 `null`을 반환한다.
