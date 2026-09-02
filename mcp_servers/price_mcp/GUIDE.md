# 주가 MCP 서버 가이드

## 역할

Price MCP는 주가와 등락 정보를 제공하는 독립 Tool 서버다. MCP Client가 공공데이터 API를 직접 호출하지 않도록 가격 데이터의 수집·정제·캐시를 전담한다.

## 데이터 제공처

- 공공데이터포털 금융위원회 주식시세정보 API
- 필요한 환경변수: `DATA_GO_KR_SERVICE_KEY`
- 기본 캐시: 종목별 1분

## 환경변수 계획

```text
DATA_GO_KR_SERVICE_KEY
PRICE_MCP_HOST=0.0.0.0
PRICE_MCP_PORT=8020
PRICE_CACHE_TTL_SECONDS=60
```

## 확정 Tool

```text
get_stock_quote
get_price_activity_snapshot
```

- `get_stock_quote`: 한 종목의 현재가, 대비, 등락률과 기준 시각을 반환한다.
- `get_price_activity_snapshot`: 지원 기업 20개의 절대 등락 활동을 반환하여 시장 관심 온도 계산에 사용한다.

정확한 입출력 JSON은 `shared/contracts/price/README.md`를 따른다.

## 목표 구조

```text
price_mcp/
├─ app/
│  ├─ tools/       # MCP Tool
│  ├─ services/    # 가격 정규화·활동도 계산·캐시
│  ├─ clients/     # 공공데이터 API 연결
│  ├─ schemas/     # Tool 입출력
│  ├─ core/        # 설정·로그
│  └─ server.py
├─ tests/
├─ .env.example
├─ requirements.txt
└─ GUIDE.md
```

## 하지 않는 일

- 뉴스·공시·커뮤니티 조회
- 사용자 로그인과 투자 성향 처리
- 매수·매도 판단
- 종합 분석 문장 생성
