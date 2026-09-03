# Frontend 개발 가이드

## 역할

Frontend는 사용자 화면만 담당하고 Backend의 `/api/v1`만 호출한다. MCP Client, MCP 서버, DB, Redis와 외부 데이터 API에는 직접 연결하지 않는다.

## 확정 화면

```text
검색 화면
  → 공개 결과
  → 상세 요청
      ├─ 비회원: 로그인 안내
      └─ 회원: 근거와 개인화 결과
```

### 검색 화면

- 기업명 또는 종목 코드 입력
- 지원 기업 20개 안내
- 로그인 버튼 또는 현재 Mock 사용자 표시

### 공개 결과

- 기업명·종목 코드
- 현재 가격·변화·등락률
- 공통 한 줄 설명
- `왜 이렇게 판단했나요?` 버튼

### 회원 상세

- 시장 온도와 근거 수준
- 뉴스·기업보고서·커뮤니티 요약과 출처
- 커뮤니티 표본과 공포탐욕 지수
- 투자 성향에 맞춘 확인 포인트
- 데이터 부족·부분 실패 안내

## 목표 구조

```text
frontend/
├─ pages/
│  ├─ home/
│  ├─ login/
│  ├─ profile/
│  └─ analysis/
├─ components/
│  ├─ common/
│  ├─ stock/
│  └─ analysis/
├─ services/backend_api/
├─ state/
├─ mocks/
├─ assets/
├─ tests/
├─ .env.example
├─ requirements.txt
├─ Dockerfile
└─ app.py
```

관리자 페이지는 이번 범위에서 제외한다.

## 환경변수

```text
BACKEND_URL=http://localhost:8000
APP_MODE=development
DEMO_MODE=true
```

Frontend `.env`에는 OpenAI, DART, 뉴스, Community Token이나 DB 비밀번호를 넣지 않는다.

## 완료 기준

1. 비회원이 로그인 없이 지원 종목을 검색한다.
2. 공개 결과에 가격과 공통 한 줄 설명이 표시된다.
3. 상세 버튼에서 로그인 여부를 구분한다.
4. Mock 로그인 후 원래 검색 종목의 상세 결과로 돌아간다.
5. 회원에게 공통 근거와 개인화 결과를 구분해 표시한다.
6. 미지원 기업과 부분 실패 메시지를 표시한다.

화면 흐름은 `docs/FRONTEND_FLOW.md`, JSON은 `shared/contracts/frontend_backend/README.md`를 따른다.
