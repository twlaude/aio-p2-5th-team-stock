# 공통 상태와 오류 계약

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

`no_data`는 정상 조회했지만 결과가 없는 상태이고 `external_api_error`는 외부 제공처 호출이 실패한 상태다. 두 상태를 같은 오류로 처리하지 않는다.

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

사용자 응답에는 API Key, 내부 Prompt, Stack Trace, DB 주소를 포함하지 않는다.

## HTTP 상태

| 상황 | HTTP |
|---|---:|
| 성공·부분 성공·결과 없음 | 200 |
| 잘못된 입력·지원하지 않는 기업 | 400 |
| 로그인 필요·잘못된 토큰 | 401 |
| 외부 서버 시간 초과 | 504 |
| 처리하지 못한 내부 오류 | 500 |

MCP Tool 자체 결과는 HTTP가 아니라 위 `status` 필드로 세부 상태를 전달한다.

## 부분 성공

네 MCP 중 하나가 실패해도 확인된 결과는 유지한다.

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
