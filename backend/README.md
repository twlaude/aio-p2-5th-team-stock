# backend — 공개 API (FastAPI, 포트 8000)

Frontend가 호출하는 유일한 서버입니다. 지원 종목 확인, 로그인(JWT), 투자 성향, 단기 Memory, 분석 요청 중계와 접근 수준별 응답을 담당하고, 실제 자료 수집·Agent 실행은 `mcp_client/`에 맡깁니다.

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env            # DATABASE_URL·REDIS_URL·MCP_CLIENT_URL 등
python run.py                   # 또는 uvicorn app.main:app --host 0.0.0.0 --port 8000
MCP_CLIENT_MODE=mock python -m pytest -q tests/
```

`run.py`는 Windows에서 psycopg 비동기 모드가 SelectorEventLoop를 요구해서 둔 진입점이고, 배포는 `uvicorn app.main:app`을 그대로 씁니다. 테스트는 `MCP_CLIENT_MODE=mock`으로 돌려야 실제 MCP Client를 때리지 않습니다.

## 폴더 지도

| 경로 | 역할 |
|---|---|
| `app/main.py` | 앱 생성, CORS, 라우터 등록 (`/api/v1` 접두사) |
| `app/routers/` | HTTP 입출력만. `auth`(로그인·가입) · `analysis`(`/companies`, `/analyses`) · `profile` · `memories` · `admin`(실황 페이지, Basic Auth) |
| `app/services/` | 업무 규칙. `auth` · `analysis`(지원 여부 확인 → MCP Client 호출 → 접근 수준 적용) · `profile` · `memory` |
| `app/repositories/` | PostgreSQL 조회·저장 (`users`·`user_profiles`·`analysis_runs`, 실황 페이지용 `system`) |
| `app/clients/` | 외부 통신. `mcp_client`(HTTP) · `redis`(단기 Memory, 이벤트 발행) |
| `app/schemas/` | 요청·응답 Pydantic 모델 |
| `app/core/` | 설정(`config.py`), DB 풀, JWT(`security.py`), 관리자 Basic Auth |
| `app/data/mock_users.json` | `AUTH_MODE=mock`일 때 쓰는 데모 계정 |
| `scripts/load_test.py` | 동시 요청·의도적 오류를 쏘는 부하 점검 |
| `tests/` | 라우터별 pytest (TestClient) |

## 환경변수 요점

- `MCP_CLIENT_MODE` — `live`면 `MCP_CLIENT_URL`로 실제 호출, `mock`이면 내장 응답
- `JWT_SECRET_KEY` — 배포에서는 긴 무작위 값으로 교체
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — 관리자 실황 페이지(`/api/v1/admin/live-status`) Basic Auth
- `CORS_ALLOWED_ORIGINS` — Frontend 주소 목록
