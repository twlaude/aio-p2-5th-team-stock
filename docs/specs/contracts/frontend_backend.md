# Frontend ↔ Backend 계약

> **한눈에**
> 비회원은 미리보기, 회원은 상세 분석입니다.
> 공개 범위·로그인 여부로 화면을 나눕니다.
> Endpoint(요청 경로)·JSON을 공유합니다.

## 공통 원칙

- 기본 주소: `http://BACKEND_HOST:8000/api/v1`
- 전송 방식: HTTP REST + JSON
- 회원 API: `Authorization: Bearer <access_token>` 사용
- 비회원도 지원 종목 분석을 요청합니다. 화면 기준은 `access_level`·`requires_login`입니다.

## Endpoint

| Method | Path | 인증 | 목적 |
|---|---|---|---|
| GET | `/health` | 없음 | Backend 상태 확인 |
| POST | `/api/v1/auth/login` | 없음 | 로그인 |
| POST | `/api/v1/auth/signup` | 없음 | 회원가입과 투자 성향 등록 |
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
    "display_name": "데모 사용자 1"
  },
  "profile_completed": true
}
```

DB는 비밀번호 해시(일방향 변환값)를 저장합니다. 발표용 10개 계정의 공통 비밀번호는 `Demo1234!`입니다.

## 회원가입

가입에는 투자 성향 네 응답이 모두 필요합니다.

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

`GET /api/v1/companies`: 2026년 9월 1일 기준 고정 목록입니다.

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

KRX 공식 자료에서 우선주·ETF·REIT를 빼고 보통주를 다시 순위 매긴 20개를 Mock/Seed(예시·초기 데이터)로 고정합니다.
`shared/supported_companies.json`(2026-09-02 확정, 20개)이 Backend Seed·Disclosure MCP 임베딩·Community MCP 지원·Price MCP 조회 대상의 공통 기준입니다.

## 종목 분석 요청

```json
{
  "query": "삼성전자"
}
```

`query`: 기업명·종목 코드. 자유 질문 필드는 없습니다. Backend는 정식 지원 기업명·코드로 변환해 MCP Client를 호출하며, 로그인 시 성향도 보냅니다.

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
    "as_of": "2026-09-01T06:30:00Z",
    "volume_basis": "last_session",
    "volume_as_of": "2026-08-31"
  },
  "one_line_summary": "공통 데이터를 바탕으로 만든 추천 없는 한 줄 설명",
  "detail": null,
  "personalized_checkpoints": null
}
```

비회원은 기업정보·현재 가격·등락·공통 한 줄만 봅니다. 상세 버튼은 `회원가입이 필요합니다!`를 안내합니다.
`price.volume_basis`·`price.volume_as_of`는 선택 필드입니다. 회원 상세는 기준이 `last_session`이고 날짜가 있을 때만 관심 온도 설명 아래에 해당 거래일을 표시합니다.

## 회원 분석 응답

`company`·`price`·`one_line_summary`는 비회원과 같습니다. 아래 필드를 추가합니다.

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

Backend가 지원 여부를 먼저 확인합니다. 미지원이면 MCP Client 호출은 없습니다.

```json
{
  "status": "unsupported_company",
  "message": "아직 이 기업의 분석 정보는 제공하지 않습니다. 현재는 2026년 9월 1일 기준 코스피 시가총액 상위 20개 기업만 지원하고 있어요.",
  "actions": ["지원 기업 20개 보기", "다른 종목 검색하기"]
}
```
