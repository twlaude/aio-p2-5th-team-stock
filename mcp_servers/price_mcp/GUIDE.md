# Price MCP 가이드

## 역할

Price MCP는 한국투자증권 실전투자 REST API에서 검색 종목의 현재 가격을 조회하고 공통 Schema로 변환하는 독립 Tool 서버다.

```text
MCP Client -> get_stock_quote -> Price MCP -> 한국투자증권 Open API
```

Price MCP는 시장 관심도, 투자 판단, 종합 분석을 만들지 않는다. 사용자 정보와 투자 성향도 받지 않는다.

## 제공 Tool

```text
get_stock_quote(company_name, stock_code)
```

- `company_name`: Backend에서 검증한 정식 기업명
- `stock_code`: 6자리 종목 코드
- 반환값: 현재가, 전일 대비, 등락률, 가격 기준 시각과 출처

## 실행 환경

```powershell
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python server.py
```

실제 `KIS_APP_KEY`, `KIS_APP_SECRET`은 `.env`에만 입력하고 Git에 올리지 않는다.

```text
MCP: http://localhost:8020/mcp
Health: http://localhost:8020/health
```

## 처리 순서

1. Tool이 기업명과 6자리 종목 코드를 검증한다.
2. Service가 종목별 60초 캐시를 확인한다.
3. Client가 저장된 접근 토큰을 확인하고 필요할 때만 재발급한다.
4. 한국투자증권 `주식현재가 시세` API를 호출한다.
5. 원본 응답을 팀 공통 Price Schema로 변환한다.
6. 인증, 시간 초과, 외부 장애를 구조화한 상태로 반환한다.

런타임 Mock Data와 Mock 모드는 제공하지 않는다. 단위 테스트에서만 외부 HTTP 응답을 가상화한다.

## Docker

```powershell
docker build -t stock-price-mcp .
docker run --env-file .env -p 8020:8020 stock-price-mcp
```

## 완료 확인

```powershell
pytest
```

마지막 실제 연동은 삼성전자 `005930`으로 확인한다. 로그와 오류 응답에는 App Key, App Secret, 접근 토큰을 남기지 않는다.
