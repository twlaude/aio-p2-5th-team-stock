# 개발 환경

> **한눈에** — 소스 빌드와 서비스별 실행 방법입니다.
> 이미지로 바로 실행하려면 [README 바로 실행](../../README.md#1-바로-실행-docker)을 봅니다.
> 서비스별 `.env`를 채우고 가상환경을 나눕니다.

### 소스에서 이미지를 직접 빌드
`compose.yml`은 7개 서비스와 PostgreSQL 이미지(`infra/postgres.Dockerfile`)를 빌드합니다. `backend/`, `mcp_client/`, `mcp_servers/*/`의 `.env.example`을 `.env`로 복사해 채웁니다.

```bash
docker compose build
docker compose up -d --wait
```

### 서비스별로 직접 실행 (Docker 없이)
각 행의 `cd`는 저장소 루트 기준입니다. Python 서비스마다 폴더에 들어가 아래 준비를 반복합니다. Disclosure MCP의 OpenAI 버전 범위와 MCP Client의 고정 버전이 달라 가상환경을 분리합니다. 키·버전은 [환경변수 표](LOCAL_RUN_ENV_CHECKLIST.md)를 봅니다.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

| 순서·폴더 | 준비·실행 |
|---|---|
| 1. `cd infra` | `cp .env.example .env` → `docker compose up -d`로 PostgreSQL/pgvector·Redis를 실행합니다. |
| 2. `cd mcp_servers/disclosure_mcp` | `python scripts/init_db.py` → `python scripts/sync_companies.py` → `python scripts/ingest_annual_reports.py --stock 005930 --years 2025`. 필요한 종목의 최신 1년치만 색인합니다. |
| 3. `mcp_servers/price_mcp/`, `mcp_servers/news_mcp/`, `mcp_servers/disclosure_mcp/`, `mcp_servers/community_mcp/` | 각 `.env.example` 확인·설정 후 `python server.py`. Price 8020 / News 8021 / Disclosure 8022 / Community 8023입니다. |
| 4. `cd mcp_client` | `python server.py` (8010). `mcp_client/.env`에 `OPENAI_API_KEY`·네 MCP URL을 설정합니다. 다른 컴퓨터에서 실행하면 주소를 바꿉니다. |
| 5. `cd backend` | `uvicorn app.main:app --host 0.0.0.0 --port 8000`. `backend/.env`에 `MCP_CLIENT_MODE=live`, `MCP_CLIENT_URL=http://localhost:8010`을 설정합니다. 배포 시 `JWT_SECRET_KEY`는 긴 무작위 값으로 바꿉니다. |
| 6. `cd frontend` | `npm ci` → `cp .env.example .env` → `npm run dev`. `frontend/.env`에 `VITE_API_MODE=live`, `VITE_BACKEND_URL=http://localhost:8000`을 설정합니다. 개발 서버는 `http://localhost:8501`입니다. |

PostgreSQL Volume 최초 생성 때 `db/schema.sql` → `db/seed.sql` 순으로 적용됩니다. 기존 Volume에는 초기화 SQL을 자동 재적용하지 않습니다.

### 연결 확인

```bash
curl http://localhost:8010/internal/v1/mcp-status
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/analyses \
  -H 'Content-Type: application/json' \
  -d '{"query":"삼성전자"}'
```
