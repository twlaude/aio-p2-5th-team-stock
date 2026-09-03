# Mock 로그인 가이드

## 확정 범위

비회원도 종목 검색과 공개 결과를 확인한다. 상세 근거나 개인화 결과를 요청할 때만 로그인을 요구한다.

```text
비회원 검색
  → 공개 결과
  → 상세 클릭
      → 회원가입이 필요합니다!
      → Mock 로그인
      → 같은 종목의 회원 상세 결과
```

## Mock 사용자

`backend/app/data/mock_users.json`의 10명을 사용한다. 사용자마다 아래 네 가지 투자 성향이 미리 준비되어 있다.

```text
experience_level
risk_profile
investment_horizon
preferred_evidence
```

아이디는 `demo001`부터 `demo010`까지이며 공통 비밀번호는 `Demo1234!`다. 이는 발표용 공개 Mock 자격증명이며 실제 사용자 인증에 재사용하지 않는다. Backend는 `DEMO_PASSWORD` 환경변수로 값을 읽는다.

## 인증 전달

- 로그인 성공 시 Backend가 데모 Access Token을 반환한다.
- Frontend는 이후 요청에 `Authorization: Bearer <access_token>`을 사용한다.
- Backend는 토큰에서 사용자 ID를 확인한다.
- 요청 본문의 임의 `user_id`를 신뢰하지 않는다.

## 이번 범위에서 보류

- 이메일 인증
- 비밀번호 찾기
- Refresh Token
- 소셜 로그인
- 운영 수준의 회원가입

## 금지 정보

원문 비밀번호, 계좌·카드 정보, API Key와 Access Token 원문을 DB나 Memory에 저장하지 않는다.
