# Price MCP Tool 계약

## 연결

- MCP 주소: `http://PRICE_MCP_HOST:8020/mcp`
- 제공처: 한국투자증권 실전투자 REST `주식현재가 시세` API
- 캐시: 종목별 60초
- 런타임 Mock Data 없음

## Tool: `get_stock_quote`

입력:

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930"
}
```

Backend가 지원 기업을 검증한 뒤 MCP Client가 정식 기업명과 6자리 종목 코드를 전달한다. Price MCP는 목록을 별도로 관리하지 않고 입력 형식만 검증한다.

성공 출력:

```json
{
  "status": "success",
  "company_name": "삼성전자",
  "stock_code": "005930",
  "current_price": 70000,
  "change": 500,
  "change_rate": 0.72,
  "volume": 15234000,
  "volume_change_rate": 118.42,
  "avg_volume_20d": 12864000,
  "volume_ratio_20d": 1.18,
  "volume_basis": "today_close",
  "volume_as_of": "2026-09-04",
  "projected_volume": null,
  "warnings": [],
  "as_of": "2026-09-04T06:30:00Z",
  "source_name": "한국투자증권 Open API",
  "collected_at": "2026-09-04T06:30:00Z"
}
```

- 금액은 원 단위 정수다.
- `change`와 `change_rate`는 상승 시 양수, 하락 시 음수, 보합 시 0이다.
- `volume`은 기준과 무관하게 현재가 응답의 실제 누적 거래량이며, `volume_change_rate`는 전일 대비 거래량 비율(%)이다. 제공처가 비율을 주지 않으면 `null`이다.
- 거래일 여부는 Asia/Seoul 기준 오늘 날짜 행이 일봉 `output2`에 있는지로 판단한다. 별도 휴장일 달력을 사용하지 않는다.

| `volume_basis` | 선택 조건 | 비율의 분자 | `avg_volume_20d` | `volume_as_of` / `projected_volume` |
|---|---|---|---|---|
| `intraday_pace` | 거래일 09:00 이상 15:30 미만 | `volume / clamp(장 시작 후 경과 비율, 0.10, 1.0)` | 오늘 이전 최대 20거래일 평균 | 오늘 / 장 마감 환산 거래량 |
| `today_close` | 거래일 15:30 이상 | 실제 누적 거래량 | 오늘 이전 최대 20거래일 평균 | 오늘 / `null` |
| `last_session` | 비거래일 또는 거래일 09:00 이전 | 오늘 이전 가장 최근 거래일의 거래량 | 그 기준일 이전 최대 20거래일 평균 | 기준 거래일 / `null` |

- `volume_ratio_20d`는 위 분자를 `avg_volume_20d`로 나누고 소수 둘째 자리로 반올림한다. 가용 평균이 없으면 평균과 비율은 `null`이며 평균이 0이면 비율만 `null`이다.
- 일봉 API 조회만 실패하면 현재가 성공은 유지하고 `avg_volume_20d`, `volume_ratio_20d`, `volume_basis`, `volume_as_of`, `projected_volume`을 `null`로 반환하며, `warnings`에 `VOLUME_BASELINE_UNAVAILABLE`을 넣는다.
- REST 현재가 응답을 받은 시각을 UTC ISO 8601로 기록한다.
- 장 마감·휴장 중에는 제공처가 반환하는 가장 최근 가격을 그대로 표시한다.

오류 출력:

```json
{
  "status": "external_api_error",
  "error": {
    "service": "price_mcp",
    "code": "KIS_API_UNAVAILABLE",
    "message": "현재 가격 정보를 일시적으로 가져오지 못했습니다.",
    "retryable": true
  }
}
```

가능한 상태는 `success`, `no_data`, `invalid_request`, `unauthorized`, `external_api_error`, `timeout`, `internal_error`다. 실제 API 실패를 가짜 가격으로 대체하지 않는다.
