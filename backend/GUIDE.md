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
MCP_CLIENT_TIMEOUT_SECONDS=75
MCP_CLIENT_MODE=mock   # mock | live. live에서 연결 실패는 Mock으로 숨기지 않고 오류로 반환한다.

LLM_PROVIDER
OPENAI_API_KEY
OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=low

AUTH_MODE
DEMO_USER_ID
JWT_SECRET_KEY

CORS_ALLOWED_ORIGINS=http://localhost:5173   # 콤마로 여러 origin 허용
```

실제 값은 `.env`에만 두고 `.env.example`에는 키 이름과 예시 형식만 작성한다.

## Docker 실행

`Dockerfile`이 `shared/supported_companies.json`을 이미지 안에 복사해야 해서 빌드 컨텍스트를 backend/가 아니라 저장소 루트로 잡는다. `backend/`에서 그냥 `docker build .`를 실행하면 실패한다.

```bash
# 저장소 루트에서 실행
docker build -f backend/Dockerfile -t stock-backend .
docker run -p 8000:8000 --env-file backend/.env stock-backend
```

## 테스트 실행 전 PostgreSQL·Redis 필요

`user_repository.py`·`analysis_repository.py`는 PostgreSQL을, `clients/redis/client.py`는 Redis를 실제로 사용한다(메모리 저장 아님). 테스트나 로컬 실행 전에 둘 다 먼저 띄운다.

```bash
cd infra
docker compose up -d
```

`DATABASE_URL`·`REDIS_URL` 기본값은 `infra/docker-compose.yml`의 기본 계정과 일치한다.

로그인 토큰은 메모리 매핑이 아니라 실제 JWT(HS256)다. `JWT_SECRET_KEY`를 배포 환경에서는 반드시 32바이트 이상의 무작위 값으로 바꾼다. `JWT_EXPIRES_MINUTES`(기본 1440 = 24시간)가 지나면 토큰이 만료되어 재로그인이 필요하다.

## 개인화는 MCP Client 책임

`나를 위한 확인 포인트`(`personalized_checkpoints`) 생성은 MCP Client가 OpenAI `gpt-5.6-luna`로 처리한다. Backend는 MCP Client 응답의 `personalized_checkpoints`를 검증만 하고 그대로 Frontend에 전달한다.

## 실황 확인 (`/api/v1/admin/live-status`)

배포 서버(root SSH만 있는 VPS 등)에서 SSH 없이 지금 무슨 일이 일어나는지 보고 싶을 때 쓴다. `ADMIN_USERNAME`/`ADMIN_PASSWORD`(Basic Auth) 뒤에 있고, 프론트 프록시를 그대로 타므로 `https://프론트주소/api/v1/admin/live-status`로 열면 된다.

- Redis `backend:short_term:*` 스냅샷 (지금 활성 단기 Memory, TTL 포함)
- PostgreSQL `analysis_runs` 최근 30건 (`status`, `partial_failures` 포함 — 어느 MCP가 왜 실패했는지 여기서 보인다)
- 이후 변화는 폴링이 아니라 **Redis Pub/Sub(`backend:live-events`) → SSE**로 실시간 push된다. `set_state()`와 `analysis_repository.save_run()`이 매번 이벤트를 발행한다.

배포 환경에서는 `.env`의 `ADMIN_USERNAME`/`ADMIN_PASSWORD`를 기본값에서 반드시 바꾼다.

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
