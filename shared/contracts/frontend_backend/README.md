# Frontend ↔ Backend 계약

## 공통 원칙

- 기본 주소: `http://BACKEND_HOST:8000/api/v1`
- 전송 방식: HTTP REST + JSON
- 회원 API: `Authorization: Bearer <access_token>` 사용
- 비회원도 지원 종목 분석을 요청할 수 있지만 공개 미리보기만 받는다.
- Frontend는 응답의 `access_level`과 `requires_login`을 기준으로 화면을 구성한다.

## Endpoint

| Method | Path | 인증 | 목적 |
|---|---|---|---|
| GET | `/health` | 없음 | Backend 상태 확인 |
| POST | `/api/v1/auth/login` | 없음 | 로그인 |
| POST | `/api/v1/auth/signup` | 없음 | 실제 회원가입(후순위 선택 구현) |
| GET | `/api/v1/profile` | 필요 | 내 투자 성향 조회 |
| PUT | `/api/v1/profile` | 필요 | 내 투자 성향 수정 |
| GET | `/api/v1/companies` | 없음 | 지원 기업 20개 조회 |
| POST | `/api/v1/analyses` | 선택 | 비회원 미리보기 또는 회원 상세 분석 |

## 로그인

요청:

```json
{
  "username": "demo001",
  "password": "Demo1234!"
}
```
응답:

```json
{
  "status": "success",
  "access_token": "demo-access-token",
  "token_type": "bearer",
  "user": {
    "user_id": "demo-001",
    "username": "demo001",
    "display_name": "안정형 장기 초보"
  },
  "profile_completed": true
}
```

Mock 사용자 목록은 `backend/app/data/mock_users.json`이다. 아이디는 `demo001`~`demo010`, 공통 비밀번호는 `Demo1234!`이며 발표용 공개 Mock 자격증명이다. Backend는 `DEMO_PASSWORD` 환경변수로 읽는다. 실제 인증을 구현할 경우 DB에는 비밀번호 해시만 저장한다.

## 실제 회원가입(후순위)

MVP는 투자 성향이 준비된 Mock 사용자 10명의 로그인까지만 필수다. 시간이 남아 실제 회원가입을 구현한다면 네 가지 투자 성향 응답을 모두 받아야 가입이 완료된다.

```json
{
  "username": "new_user",
  "password": "사용자가_입력한_비밀번호",
  "display_name": "새 사용자",
  "profile": {
    "experience_level": "beginner",
    "risk_profile": "balanced",
    "investment_horizon": "long",
    "preferred_evidence": "news"
  }
}
```

## 지원 기업 목록

`GET /api/v1/companies`는 고정된 2026년 9월 1일 기준 지원 기업 목록을 반환한다.

```json
{
  "status": "success",
  "snapshot_date": "2026-09-01",
  "companies": [
    {
      "rank": 1,
      "company_name": "회사명",
      "stock_code": "000000",
      "market": "KOSPI"
    }
  ]
}
```

확정 목록은 `shared/supported_companies.json`이다(2026-09-02 확정, 20개). 목록의 기준과 출처는 JSON의 `criteria`, `source` 필드를 따른다. Backend Seed와 Disclosure MCP 임베딩 대상은 이 Snapshot을 기준으로 한다.

## 종목 분석 요청

```json
{
  "query": "삼성전자",
  "question": "최근 주가 변동을 볼 때 어떤 내용을 확인해야 하나요?"
}
```

`question`은 선택값이다. 없으면 기본 종목 분석을 수행한다. Backend는 기업명을 지원 기업의 정식 이름과 종목 코드로 변환한 뒤 MCP Client를 호출한다.

## 비회원 분석 응답

```json
{
  "request_id": "uuid",
  "status": "success",
  "access_level": "guest",
  "requires_login": true,
  "company": {
    "company_name": "삼성전자",
    "stock_code": "005930",
    "supported": true
  },
  "price": {
    "current_price": 0,
    "change": 0,
    "change_rate": 0.0,
    "as_of": "2026-09-01T06:30:00Z"
  },
  "one_line_summary": "공통 데이터를 바탕으로 만든 추천 없는 한 줄 설명",
  "detail": null,
  "personalized_checkpoints": null
}
```

비회원 화면에는 기업정보, 현재 가격·등락, 공통 한 줄 설명만 표시한다. 상세 근거 버튼을 누르면 `회원가입이 필요합니다!`를 안내한다.

## 회원 분석 응답

회원 응답의 `company`, `price`, `one_line_summary`는 비회원과 같고 아래 필드가 추가된다.

```json
{
  "access_level": "member",
  "requires_login": false,
  "detail": {
    "market_temperature": {
      "score": 72,
      "label": "관심 높음",
      "data_coverage": ["price", "news", "community"]
    },
    "evidence_level": {
      "level": "high",
      "reason": "최근 공식 공시에서 핵심 내용을 확인할 수 있습니다."
    },
    "news_summary": "뉴스 요약",
    "disclosure_summary": "전자공시와 기업보고서 요약",
    "community_summary": "커뮤니티 반응 요약",
    "sources": []
  },
  "personalized_checkpoints": {
    "personal_summary": "회원 성향에 맞춘 한 줄 해석",
    "priority_checks": ["확인 항목 1", "확인 항목 2"],
    "caution": "주의할 점 1개"
  }
}
```

## 지원하지 않는 기업

Backend는 지원 여부를 먼저 확인하고 MCP Client를 호출하지 않는다.

```json
{
  "status": "unsupported_company",
  "message": "아직 이 기업의 분석 정보는 제공하지 않습니다. 현재는 2026년 9월 1일 기준 코스피 시가총액 상위 20개 기업만 지원하고 있어요.",
  "actions": ["지원 기업 20개 보기", "다른 종목 검색하기"]
}
```
