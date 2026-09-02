# Backend 가이드

## 역할

Backend는 Frontend의 유일한 서버 진입점이다. 사용자 구분, 투자 성향, Memory, MCP Client 요청, 개인화 결과 조립을 담당한다.

MCP 서버를 직접 여러 개 호출하지 않고 독립 실행 중인 `mcp_client` 통합 서버에 분석을 요청한다.

## 주요 책임

- 데모 사용자 또는 실제 로그인 사용자 식별
- 투자 성향 등록·조회·수정·삭제
- PostgreSQL 장기 Memory 조회
- Redis 단기 상태 조회
- MCP Client에 공통 종목 분석 요청
- 관련 Memory만 선택
- `나를 위한 확인 포인트` 생성
- 최종 응답과 출처를 Frontend에 반환

## 구현 시 목표 구조

```text
backend/
├─ app/
│  ├─ routers/             # 인증·프로필·분석·Memory API
│  ├─ schemas/             # 요청·응답 형식
│  ├─ services/            # 인증·Memory·개인화 업무 로직
│  ├─ repositories/        # PostgreSQL 접근
│  ├─ clients/             # MCP Client·LLM·Redis 연결
│  ├─ core/                # 환경설정·보안·로그
│  └─ main.py
├─ tests/
├─ .env.example
├─ requirements.txt
├─ AUTH_GUIDE.md
└─ MEMORY_GUIDE.md
```

## Backend 분석 흐름

```text
Frontend 요청
  → 사용자 확인
  → 종목명·질문 검증
  → 투자 성향과 관련 Memory 조회
  → MCP Client에 공통 분석 요청
  → 공통 분석 수신
  → 개인화 확인 포인트 생성
  → 최종 응답 저장·반환
```

## MCP Client 요청 원칙

MCP Client에는 가능한 한 사용자 개인정보를 보내지 않는다.

보내는 정보 예시:

- 기업명
- 종목 코드
- 분석 질문
- 데이터 조회 기간

보내지 않는 정보 예시:

- 비밀번호
- 인증 토큰
- 사용자 전체 프로필
- 개인정보
- 사용자 전체 대화 기록

## 환경변수 계획

```text
DATABASE_URL
REDIS_URL
REDIS_TTL_SECONDS

MCP_CLIENT_URL
MCP_CLIENT_TIMEOUT_SECONDS

LLM_PROVIDER
OPENAI_API_KEY
OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=low

AUTH_MODE
DEMO_USER_ID
JWT_SECRET_KEY
```

실제 값은 `.env`에만 두고 `.env.example`에는 키 이름과 예시 형식만 작성한다.

## 개인화 LLM과 토큰 절감 규칙

회원별 `나를 위한 확인 포인트` 생성에도 OpenAI의 `gpt-5.6-luna`를 사용한다. Backend는 개인화에 필요한 최소 정보만 LLM에 전달한다.

- 회원의 네 가지 성향 값: 투자 경험, 위험 성향, 투자 기간, 선호 근거
- MCP Client가 만든 공통 한 줄 분석과 핵심 근거
- 개인화 출력 규격: `personal_summary` 1개, `priority_checks` 2개, `caution` 1개

전체 대화 기록, 뉴스 원문 전체, 커뮤니티 원문, 기업보고서 전체는 개인화 호출에 다시 넣지 않는다. 동일한 회원 성향·종목·공통 분석 버전에 대한 개인화 결과는 캐시할 수 있으며, 입력·출력·추론 토큰 사용량을 기록한다.

## Backend에서 하지 않는 일

- 뉴스·DART·커뮤니티 원본 직접 수집
- 네 MCP 서버의 결과 통합
- Frontend 화면 렌더링
- 주식 매수·매도 추천

## 완료 기준

1. 사용자별 투자 성향이 섞이지 않는다.
2. 투자 성향이 없을 때 Frontend가 온보딩 여부를 판단할 수 있다.
3. MCP Client 장애를 구분해 반환한다.
4. 공통 분석과 개인화 결과를 별도 필드로 반환한다.
5. 사용자가 Memory를 조회·수정·삭제할 수 있다.
