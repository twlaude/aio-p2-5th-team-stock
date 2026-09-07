# mcp_servers — 데이터 제공 MCP 서버 4개

각 폴더가 독립 서버이며 구조가 같습니다: `server.py`(진입점) → `app/tools/`(MCP Tool 정의) → `app/services/`(정제·집계) → `app/clients/`(외부 API). 설정은 `app/core/config.py`, 응답 모델은 `app/schemas/`, 테스트는 `tests/`입니다. 모든 서버는 `health` Tool과 `/health`를 제공합니다.

| 서버 | 포트 | 외부 자료 | Tool |
|---|---:|---|---|
| `price_mcp/` | 8020 | 한국투자증권 Open API | `get_stock_quote` (종목별 60초 캐시) |
| `news_mcp/` | 8021 | NAVER 뉴스 검색 API | `search_news` (중복·무관 기사 제외) |
| `disclosure_mcp/` | 8022 | OpenDART + 전용 PostgreSQL(pgvector) | `get_recent_disclosures` · `get_disclosure_detail` · `search_periodic_report` · `search_annual_report` |
| `community_mcp/` | 8023 | 네이버 종목토론방 집계 서버 | `get_community_reaction` · `get_fear_greed_index` |

## 실행 (서버마다 동일)

```bash
cd price_mcp                    # news_mcp / disclosure_mcp / community_mcp
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env            # API 키·포트
python server.py
python -m pytest -q tests/
```

News·Community는 `NEWS_MOCK=true` / `COMMUNITY_MOCK=true`로 키 없이 가짜 응답을 낼 수 있습니다. 가상환경은 서버별로 따로 두는 것이 안전합니다 (Disclosure의 OpenAI 패키지 범위가 MCP Client와 다릅니다).

## disclosure_mcp만 있는 것

- `db/schema.sql` — 전용 DB(`companies`·`disclosures`·`annual_reports`·`report_chunks`). Backend DB와 분리
- `app/rag/` — 보고서 파싱(`parser`) → 청크(`chunker`) → pgvector 저장·검색(`store`)
- `scripts/` — `init_db.py`(스키마 적용) → `sync_companies.py`(지원 20종목 corp_code) → `ingest_annual_reports.py`(보고서 색인) 순서. `smoke.py`는 기동 중인 서버의 Tool 전수 점검
