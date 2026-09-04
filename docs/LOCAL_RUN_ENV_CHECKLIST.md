# 전체 스택 로컬 실행 · env 체크리스트 (2026-09-04 VPS 통합 테스트 기준)

Frontend → Backend → MCP Client → MCP 4개를 한 컴퓨터에서 붙여 본 결과를 바탕으로, 다시 띄울 때 필요한 것만 적었다. Agent(MCP Client) 부분은 아직 다듬는 중이므로 이 문서는 "붙이는 데 필요한 것"에 한정한다.

## 0. 역할 정리 (2026-09-04 합의)

- **MCP 서버 4개는 VPS에서 상시 실행** (systemd, 24/7). 팀원은 띄우지 않고 URL만 쓴다.
- **오현님**: `mcp_client`만 로컬에서 실행하며 Agent 마무리. 화면 보면서 하려면 backend + frontend도 로컬에 (infra compose로 PG·Redis).
- **태웅**: VPS의 MCP 4개·데모 스택 운영, 프론트.

| MCP | VPS 주소 (mcp_client `.env`에 그대로) | 상태 |
|---|---|---|
| Price | `PRICE_MCP_URL=http://159.223.75.71:8020/mcp` | KIS 키 대기 → 그때까지 **테스트 스텁**(70,000원 고정, `[TEST] price stub`). 오현님 KIS 키를 받으면 실서버로 교체 |
| News | `NEWS_MCP_URL=http://159.223.75.71:8021/mcp` | NAVER API HUB 키 없음 → mock 3건. 키 생기면 VPS `.env`에 넣고 재시작 |
| Disclosure | `DISCLOSURE_MCP_URL=http://159.223.75.71:8022/mcp` | 실데이터. DART 최근 공시 + 20종목 2025 사업보고서 색인 |
| Community | `COMMUNITY_MCP_URL=http://159.223.75.71:8023/mcp` | 실데이터 (네이버 종토방 FGI) |

상태 확인: `curl http://159.223.75.71:802N/health`. 인증 없음 — 발표용 공개 데모 범위에서만 쓴다.

### 오현님 mcp_client 로컬 실행에 필요한 것

```text
mcp_client/.env
  OPENAI_API_KEY=<본인 키>          # 모델·effort는 기본값(gpt-5.6-luna, low) 그대로
  PRICE_MCP_URL=http://159.223.75.71:8020/mcp
  NEWS_MCP_URL=http://159.223.75.71:8021/mcp
  DISCLOSURE_MCP_URL=http://159.223.75.71:8022/mcp
  COMMUNITY_MCP_URL=http://159.223.75.71:8023/mcp
```

그 외 키(DART·NAVER·커뮤니티 토큰)는 전부 VPS 쪽에 있으니 오현님은 필요 없다. 화면까지 보려면 `backend/.env`(`MCP_CLIENT_MODE=live`, `MCP_CLIENT_URL=http://localhost:8010`)와 `frontend/.env`(`VITE_API_MODE=live`)만 추가.

## 1. VPS 데모 (지금 붙어 있는 상태)

- 화면: http://159.223.75.71:8501 (React, `VITE_API_MODE=live`)
- 로그인: `demo001` ~ `demo010` / `Demo1234!` (db/seed.sql)
- 어디까지 진짜 데이터인지

| 구간 | 상태 |
|---|---|
| Price MCP | **테스트 스텁** — KIS 키가 없어 70,000원 고정값. 실서버 아님 |
| News MCP | NAVER API HUB 키 없음 → `NEWS_MOCK=auto`로 mock 3건 |
| Community MCP | 실데이터 (태웅 VPS FGI API `:8877`, 네이버 종토방 집계) |
| Disclosure MCP | 실데이터 (DART 최근 공시 + 삼성전자 2025 사업보고서 색인) |
| MCP Client LLM | OpenAI 호출이 400으로 실패해 **규칙 기반 폴백 문장**이 나옴 (아래 4-②) |
| Backend | 실코드 (PG `stock_insight_team`, Redis, JWT) |

## 2. 실행 순서 (로컬 한 대)

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

## 3. 서비스별 .env — 실제로 채워야 하는 값

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

## 4. 붙여 보면서 확인한 것 (Agent 다듬을 때 참고)

1. **가격이 없으면 전부 실패한다.** `mcp_client/app/workflows/analysis.py`가 `price.status != success`면 `RequiredPriceError` → Backend 503. 계약대로지만 KIS 키 없는 PC에서는 아무 화면도 못 본다. 개발 편의로 `PRICE_MOCK` 같은 스위치를 둘지는 결정 필요.
2. **OpenAI Responses 400 — strict JSON schema.** `mcp_client/app/providers/openai.py`의 `_text_format()`이 `strict: true`인데 `Narrative.model_json_schema()`에 `additionalProperties: false`가 없어 400이 난다.
   오류 원문: `Invalid schema for response_format 'stock_information_analysis': In context=(), 'additionalProperties' is required to be supplied and to be false.`
   Narrative(및 중첩 모델)에 `model_config = ConfigDict(extra="forbid")`를 주면 pydantic이 `additionalProperties: false`를 넣어 준다. 이게 풀려야 Agent 서사·Tool 호출 루프가 실제로 돈다.
3. **폴백 문장 조사.** 규칙 기반 문장이 "삼성전자은 …"으로 나온다 (은/는). LLM이 붙으면 사라지지만 폴백도 쓰인다면 조사 처리 필요.
4. **사업보고서는 최신 1년치(2025)만 색인한다.** `ingest_annual_reports.py --stock 005930 --years 2025`. 2024 이전 보고서는 파서가 섹션을 못 찾아 실패하지만, 1년치만 쓰기로 해서 고치지 않는다.
5. **프론트 live 어댑터(태웅 담당)**: 재료 표시줄 "뉴스 0건·공시 0건", 분위기 vs 근거 카드 "공시 없음"은 mock 기준 조립이라 백엔드 응답 구조에 맞춰 손볼 예정. `display_name`도 seed 값("데모 사용자 1")이 그대로 나온다.

## 5. 검증 명령

```bash
curl localhost:8010/internal/v1/mcp-status              # 4개 MCP 연결 상태
curl -X POST localhost:8000/api/v1/analyses -H 'Content-Type: application/json' -d '{"query":"삼성전자"}'
```
