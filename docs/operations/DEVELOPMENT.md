# 개발 환경

소스를 고치거나 이미지를 직접 만들 때의 실행 방법입니다. 서비스만 써 보려면 루트 README의 "바로 실행"으로 충분합니다.

### 소스에서 이미지를 직접 빌드

`compose.yml`은 7개 서비스와 PostgreSQL 이미지(`infra/postgres.Dockerfile`)를 저장소 소스에서 빌드합니다. 각 서비스의 값은 서비스 폴더의 `.env`에서 읽으므로 `backend/`, `mcp_client/`, `mcp_servers/*/`의 `.env.example`을 `.env`로 복사해 채웁니다.

```bash
docker compose build
docker compose up -d --wait
```

### 서비스별로 직접 실행 (Docker 없이)

Python 서비스는 의존성 버전이 서로 다를 수 있으므로 서비스별 가상환경을 사용하는 것이 안전합니다. 특히 Disclosure MCP의 OpenAI 패키지 범위와 MCP Client의 고정 버전은 다릅니다.

**1) PostgreSQL·Redis**

```bash
cd infra
cp .env.example .env
docker compose up -d
```

PostgreSQL Volume을 처음 만들 때 `db/schema.sql`과 `db/seed.sql`이 순서대로 적용됩니다. 기존 Volume에는 초기화 SQL이 자동으로 다시 적용되지 않습니다.

**2) MCP Client**

```bash
cd mcp_client
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python server.py
```

`mcp_client/.env`에는 `OPENAI_API_KEY`와 Price·News·Disclosure·Community MCP URL을 설정합니다. MCP 4개를 다른 컴퓨터에서 실행하면 그 주소로 바꿉니다.

**3) Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

실제 MCP Client를 호출하려면 `backend/.env`에서 `MCP_CLIENT_MODE=live`, `MCP_CLIENT_URL=http://localhost:8010`을 설정합니다. 배포 환경에서는 `JWT_SECRET_KEY`를 충분히 긴 무작위 값으로 바꿉니다.

**4) Frontend**

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

실제 Backend를 호출하려면 `frontend/.env`에서 `VITE_API_MODE=live`, `VITE_BACKEND_URL=http://localhost:8000`을 설정합니다. 개발 서버는 `http://localhost:8501`에서 열립니다.

**5) 연결 확인**

```bash
curl http://localhost:8010/internal/v1/mcp-status
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/analyses \
  -H 'Content-Type: application/json' \
  -d '{"query":"삼성전자"}'
```

MCP 4개를 모두 로컬에서 실행하려면 각 폴더의 `.env.example`을 확인한 뒤 `python server.py`를 실행합니다. 포트는 Price 8020, News 8021, Disclosure 8022, Community 8023으로 고정합니다.
