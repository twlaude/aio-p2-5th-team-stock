# Price MCP Tool 계약

## 연결

- MCP 주소: `http://PRICE_MCP_HOST:8020/mcp`
- 제공처: 공공데이터포털 금융위원회 주식시세정보 API
- 캐시: 종목별 1분

## Tool 1: `get_stock_quote`

입력:

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930"
}
```
출력:

```json
{
  "status": "success",
  "company_name": "삼성전자",
  "stock_code": "005930",
  "current_price": 0,
  "change": 0,
  "change_rate": 0.0,
  "as_of": "2026-09-01T06:30:00Z",
  "source_name": "공공데이터포털 금융위원회 주식시세정보",
  "collected_at": "2026-09-01T06:31:00Z"
}
```

휴장 또는 장 마감 이후에는 제공처가 반환한 가장 최근 거래 기준 시각을 `as_of`에 표시한다.

## Tool 2: `get_price_activity_snapshot`

지원 기업 20개의 6자리 종목 코드를 배열로 받아 종목별 절대 등락률을 반환한다. MCP Client는 이 값을 뉴스 활동도와 커뮤니티 언급량에 결합해 시장 관심 온도를 계산한다.

```json
{
  "stock_codes": ["005930", "000000"]
}
```

```json
{
  "status": "success",
  "items": [
    {
      "stock_code": "005930",
      "change_rate": 1.25,
      "absolute_change_rate": 1.25
    }
  ],
  "as_of": "2026-09-01T06:30:00Z",
  "collected_at": "2026-09-01T06:31:00Z"
}
```
