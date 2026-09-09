# 전체 스택 로컬 실행 · env 체크리스트

Frontend → Backend → MCP Client → MCP 4개를 붙일 때 필요한 것만 적었다. 서비스 7개는 각각 독립 프로세스라 한 컴퓨터에 모아 띄워도 되고 컴퓨터마다 나눠 띄워도 되며, 나눠 띄우면 `.env`의 주소만 바꾼다.

## 1. 실행 순서 (로컬 한 대)

```text
infra:      cd infra && cp .env.example .env && docker compose up -d      # PG(pgvector)+Redis
disclosure: cd mcp_servers/disclosure_mcp && python scripts/init_db.py && python scripts/sync_companies.py
            python scripts/ingest_annual_reports.py --stock 005930 --years 2025   # 최신 1년치만, 필요한 종목만
MCP 4개:    각 폴더에서 python server.py            (8020 price / 8021 news / 8022 disclosure / 8023 community)
mcp_client: cd mcp_client && python server.py       (8010)
backend:    cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
frontend:   cd frontend && npm ci && npm run dev    (8501, .env에 VITE_API_MODE=live)
```

각 서비스는 자기 폴더의 `requirements.txt`로 venv를 따로 만드는 게 안전하다 (disclosure는 `openai<2`, mcp_client는 `openai==2.24` 로 핀이 다름).

## 2. 서비스별 .env — 실제로 채워야 하는 값

`.env.example`을 복사한 뒤 아래 값만 채우면 된다. 나머지는 기본값으로 동작.

| 서비스 | 키 | 어디서 | 비우면 |
|---|---|---|---|
| backend | `DATABASE_URL` | infra compose 기본값 `postgresql://postgres:postgres@localhost:5432/stock_insight` | 로그인/분석 전부 실패 |
| backend | `MCP_CLIENT_MODE=live` | 직접 설정 | `mock`이면 MCP Client를 안 부르고 가짜 응답 |
| backend | `OPENAI_API_KEY` | 개인 키 | 개인화 문장 생성 폴백 |
| backend | `JWT_SECRET_KEY` | 아무 긴 문자열 | 기본값으로 동작(데모만) |
| backend | `CORS_ALLOWED_ORIGINS` | `http://localhost:8501` 추가 | 프론트를 프록시 없이 직접 붙일 때만 필요 |
| mcp_client | `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-5.6-luna` | 개인 키 | Agent 없이 규칙 기반 폴백 |
| mcp_client | `*_MCP_URL` 4개 | 기본값 localhost:8020~8023 | 다른 PC에 나눠 띄우면 IP로 교체 |
| price_mcp | `KIS_APP_KEY`, `KIS_APP_SECRET` | 한국투자증권 개발자센터 | **분석 전체가 503** (가격은 필수, mock 없음) |
| news_mcp | `NAVER_NEWS_CLIENT_ID`, `NAVER_NEWS_CLIENT_SECRET` | NAVER API HUB(ntruss) — 구 developers.naver.com 키와 다름 | mock 뉴스 3건 (`NEWS_MOCK=auto`) |
| disclosure_mcp | `DART_API_KEY`(40자) | OpenDART | 공시 도구 실패 |
| disclosure_mcp | `DATABASE_URL`, `OPENAI_API_KEY` | pgvector DB + 임베딩 키 | 사업보고서 검색 실패 |
| community_mcp | `COMMUNITY_API_URL=http://159.223.75.71:8877`, `COMMUNITY_API_TOKEN` | 토큰은 태웅에게 개인적으로 받기 (Git 금지) | mock 반응 (`COMMUNITY_MOCK=auto`) |
| frontend | `VITE_API_MODE=live`, `VITE_BACKEND_URL=http://localhost:8000` | 직접 설정 | `mock`이면 백엔드 없이 fixture |

## 3. 검증 명령

```bash
curl localhost:8010/internal/v1/mcp-status              # 4개 MCP 연결 상태
curl -X POST localhost:8000/api/v1/analyses -H 'Content-Type: application/json' -d '{"query":"삼성전자"}'
```
