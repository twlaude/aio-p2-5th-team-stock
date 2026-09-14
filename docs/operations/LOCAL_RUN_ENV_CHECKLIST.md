# 전체 스택 로컬 실행 · env 체크리스트

> **한눈에** — Frontend → Backend → MCP Client → MCP 4개를 연결합니다.
> 독립 프로세스 7개를 한 컴퓨터나 여러 컴퓨터에서 실행합니다.
> `.env` 주소와 아래 키를 채우고 연결을 확인합니다.

실행 순서·명령은 [개발 환경](DEVELOPMENT.md#서비스별로-직접-실행-docker-없이)을 봅니다. 서비스별 `requirements.txt`로 venv(가상환경)를 분리합니다. Disclosure는 `openai<2`, MCP Client는 `openai==2.24`로 버전 지정이 다릅니다.
`.env.example`을 복사해 아래 값을 채웁니다. 나머지는 기본값을 씁니다.

| 서비스 | 키 | 어디서 | 비우면 |
|---|---|---|---|
| backend | `DATABASE_URL` | infra 기본값 `postgresql://postgres:postgres@localhost:5432/stock_insight` | 로그인·분석 전부 실패 |
| backend | `MCP_CLIENT_MODE=live` | 직접 설정 | `mock`이면 MCP Client 없이 가짜 응답 |
| backend | `OPENAI_API_KEY` | 개인 키 | 개인화 문장 폴백(대체 문장) |
| backend | `JWT_SECRET_KEY` | 긴 문자열 | 기본값 동작(데모만) |
| backend | `CORS_ALLOWED_ORIGINS` | `http://localhost:8501` 추가 | 프록시 없이 직접 연결할 때만 필요 |
| mcp_client | `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-5.6-luna` | 개인 키 | Agent 없이 규칙 기반 폴백 |
| mcp_client | `*_MCP_URL` 4개 | 기본 localhost:8020~8023 | 다른 PC에서 실행하면 해당 IP로 교체 |
| price_mcp | `KIS_APP_KEY`, `KIS_APP_SECRET` | 한국투자증권 개발자센터 | **분석 전체 503** (가격 필수, mock 없음) |
| news_mcp | `NAVER_NEWS_CLIENT_ID`, `NAVER_NEWS_CLIENT_SECRET` | NAVER API HUB(ntruss), 구 developers.naver.com 키와 다름 | mock 뉴스 3건 (`NEWS_MOCK=auto`) |
| disclosure_mcp | `DART_API_KEY`(40자) | OpenDART | 공시 도구 실패 |
| disclosure_mcp | `DATABASE_URL`, `OPENAI_API_KEY` | pgvector DB·임베딩 키 | 사업보고서 검색 실패 |
| community_mcp | `COMMUNITY_API_URL=http://159.223.75.71:8877`, `COMMUNITY_API_TOKEN` | 토큰은 태웅에게 개인적으로 받습니다(Git 금지) | mock 반응 (`COMMUNITY_MOCK=auto`) |
| frontend | `VITE_API_MODE=live`, `VITE_BACKEND_URL=http://localhost:8000` | 직접 설정 | `mock`이면 Backend 없이 fixture(예시 데이터) |

연결 검증은 [개발 환경의 명령](DEVELOPMENT.md#연결-확인)을 씁니다. `curl localhost:8010/internal/v1/mcp-status`로 네 MCP를 확인하고, `POST /api/v1/analyses`에 `{"query":"삼성전자"}`를 보내 전체 왕복을 확인합니다.
