# stock_insight

종목명 하나를 입력하면 재무·뉴스·커뮤니티 분위기(공포탐욕지수)를 근거와 함께
쉽게 풀어주는 종목 딥다이브 서비스. (종목 추천 아님 — 입력 종목 분석 전용)

## 구조 (컴포넌트별 독립 실행 — 서로 다른 머신에서 돌 수 있음)
```
backend/     FastAPI 분석 API    app/{core,routers,schemas,services,clients} + scripts/
frontend/    Streamlit UI
mcp_server/
  stock_mcp/ MCP 툴 서버 :8050   app/{core,clients,schemas,services,tools} + stock_server.py
db/          PostgreSQL + pgvector 스키마/시드 SQL
```
각 컴포넌트가 자기 .env.example / requirements.txt 를 가진다 (머신 분리 실행 가능).

## 실행 (각 컴포넌트 폴더에서)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 값 채우기
```
- backend:    `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- frontend:   `streamlit run app.py`
- mcp_server: `cd stock_mcp && python stock_server.py`

DB 초기화: `psql "$DATABASE_URL" -f db/schema.sql && psql "$DATABASE_URL" -f db/seed.sql`
