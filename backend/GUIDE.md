# Backend 개발 가이드

## 역할

Backend는 Frontend가 호출하는 유일한 서버다. 지원 기업 검증, Mock 로그인, 투자 성향, Memory, MCP Client 호출과 회원 개인화를 담당한다.

## 확정 흐름

```text
Frontend 요청
  → 기업명·종목 코드 확인
  → 지원 기업 20개 검증
  → MCP Client에 사용자 정보 없이 공통 분석 요청
  → 비회원: 공개 결과 반환
  → 회원: 투자 성향·관련 Memory 조회
           → 개인화 확인 포인트 생성
           → 상세 결과 반환
```

## 확정 API

| Method | Path | 목적 |
|---|---|---|
| GET | `/health` | 상태 확인 |
| GET | `/api/v1/companies` | 지원 기업 20개 |
| POST | `/api/v1/analyses` | 비회원·회원 종목 분석 |
| POST | `/api/v1/auth/login` | Mock 로그인 |
| GET | `/api/v1/profile` | 투자 성향 조회 |
| PUT | `/api/v1/profile` | 투자 성향 수정 |
| GET | `/api/v1/memories` | Memory 조회 |
| DELETE | `/api/v1/memories/{memory_id}` | Memory 삭제 |

발표 필수 구현은 기업 목록, 분석, Mock 로그인과 프로필 조회다. 실제 회원가입과 Memory 수정·삭제 화면은 시간이 남을 때 구현한다.

## 목표 구조

```text
backend/
├─ app/
│  ├─ routers/
│  ├─ schemas/
│  ├─ services/
│  ├─ repositories/
│  ├─ clients/
│  │  ├─ mcp_client/
│  │  ├─ llm/
│  │  └─ redis/
│  ├─ data/               # Mock 사용자 등 Backend 전용 데이터
│  ├─ core/
│  └─ main.py
├─ tests/
├─ .env.example
├─ requirements.txt
├─ Dockerfile
└─ GUIDE.md
```

## MCP Client에 보내는 정보

```text
request_id
company_name
stock_code
question
requested_at
```

사용자 ID, 비밀번호, 인증 토큰, 투자 성향, 전체 대화와 Memory는 보내지 않는다.

## 개인화 입력과 출력

입력은 회원의 네 가지 성향 값과 MCP Client의 공통 분석으로 제한한다.

```text
experience_level
risk_profile
investment_horizon
preferred_evidence
common_analysis
```

출력:

```text
personal_summary
priority_checks  # 2개
caution          # 1개
```

## 환경변수

`.env.example`의 이름을 그대로 사용한다. 실제 API Key와 비밀번호는 `.env`에만 둔다.

## 하지 않는 일

- 네 MCP 서버 직접 호출
- 뉴스·DART·커뮤니티·가격 원본 수집
- 네 데이터의 공통 시장 온도 계산
- 화면 렌더링
- 포트폴리오·매매내역·주문 관리
- 매수·매도 추천

## 완료 기준

1. 미지원 기업이면 MCP Client를 호출하지 않는다.
2. 비회원과 회원 응답 범위를 구분한다.
3. Mock 사용자 10명의 성향이 섞이지 않는다.
4. MCP Client 장애와 부분 성공을 구분한다.
5. 공통 분석과 개인화 결과를 별도 필드로 반환한다.

세부 JSON은 `shared/contracts/frontend_backend/README.md`와 `shared/contracts/analysis/README.md`를 따른다.
