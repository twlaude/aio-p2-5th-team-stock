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

MCP Client는 공통 분석과 개인화 확인 항목을 모두 만든다. Backend는 사용자를 확인하고 투자 성향을 조회해서 MCP Client에 전달하며, 개인화 문장을 직접 생성하지 않는다.

보내는 정보 예시:

- 기업명
- 종목 코드
- 투자 성향(`experience_level`, `risk_profile`, `investment_horizon`, `preferred_evidence`) — 비회원은 `null`

보내지 않는 정보 예시:

- 아이디, 비밀번호
- 인증 토큰
- 개인정보
- 사용자 전체 대화 기록

MCP Client가 받은 투자 성향은 가격·뉴스·기업보고서·커뮤니티 MCP 서버에는 전달하지 않는다.

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

## 개인화는 MCP Client 책임

`나를 위한 확인 포인트`(`personalized_checkpoints`) 생성은 MCP Client가 OpenAI `gpt-5.6-luna`로 처리한다. Backend는 MCP Client 응답의 `personalized_checkpoints`를 검증만 하고 그대로 Frontend에 전달한다.

## Backend에서 하지 않는 일

- 뉴스·DART·커뮤니티 원본 직접 수집
- 네 MCP 서버의 결과 통합
- 개인화 확인 포인트 생성(LLM 호출)
- Frontend 화면 렌더링
- 주식 매수·매도 추천

## 완료 기준

1. 사용자별 투자 성향이 섞이지 않는다.
2. 투자 성향이 없을 때 Frontend가 온보딩 여부를 판단할 수 있다.
3. MCP Client 장애를 구분해 반환한다.
4. 공통 분석과 개인화 결과를 별도 필드로 반환한다.
5. 사용자가 Memory를 조회·수정·삭제할 수 있다.
