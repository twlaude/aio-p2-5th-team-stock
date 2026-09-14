# 공통 상태와 오류 계약

> **한눈에**
> 결과 없음·호출 실패를 구분합니다.
> HTTP 코드와 MCP 상태를 확인합니다.
> MCP 4개 중 하나가 실패해도 확인된 결과는 유지합니다.

## 상태값

```text
success
partial_success
no_data
unsupported_company
invalid_request
unauthorized
external_api_error
timeout
internal_error
```

`no_data`: 정상 조회·결과 없음. `external_api_error`: 외부 호출 실패.

## 오류 응답

```json
{
  "request_id": "uuid",
  "status": "external_api_error",
  "error": {
    "service": "news_mcp",
    "code": "NAVER_API_UNAVAILABLE",
    "message": "뉴스 정보를 일시적으로 가져오지 못했습니다.",
    "retryable": true
  }
}
```

API Key(인증키)·내부 Prompt(지시문)·Stack Trace(오류 추적)·DB 주소는 응답에서 숨깁니다.

## HTTP 상태

| 상황 | HTTP |
|---|---:|
| 성공·부분 성공·결과 없음 | 200 |
| 잘못된 입력·지원하지 않는 기업 | 400 |
| 로그인 필요·잘못된 토큰 | 401 |
| 외부 서버 시간 초과 | 504 |
| 처리하지 못한 내부 오류 | 500 |

MCP Tool 세부 상태는 HTTP 대신 `status`로 전달합니다.

## 부분 성공

```json
{
  "status": "partial_success",
  "partial_failures": [
    {
      "service": "community_mcp",
      "status": "timeout",
      "message": "커뮤니티 반응은 이번 분석에서 제외되었습니다."
    }
  ]
}
```
