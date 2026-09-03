# 뉴스 MCP 서버 가이드

## 목적

검색한 기업의 최근 뉴스를 조회하고, MCP Client가 분석할 수 있는 공통 형식으로 반환한다.

## 담당 범위

- 기업명과 종목 코드로 뉴스 검색
- 제목, 언론사, 발행 시각, 원문 URL 수집
- 같은 기사와 비슷한 이슈 중복 처리
- 검색 기간 적용
- 회사와 실제로 관련 있는 기사만 남기기
- 원문 또는 요약 반환

## 확정 Tool

```text
search_news
```

입출력은 `shared/contracts/news/README.md`를 따른다. MVP에서는 기사 본문 전체 조회 Tool을 만들지 않는다.

## 반환해야 할 핵심 정보

```text
headline
publisher
published_at
summary
source_url
relevance
collected_at
```

## 환경변수 계획

```text
NAVER_NEWS_CLIENT_ID
NAVER_NEWS_CLIENT_SECRET
NEWS_MCP_HOST=0.0.0.0
NEWS_MCP_PORT=8021
NEWS_LOOKBACK_DAYS=7
NEWS_RESULT_LIMIT=10
```

## Mock 단계

삼성전자 뉴스 3~5개를 고정 데이터로 반환하여 MCP Client 연결부터 확인한다.

## 완료 기준

1. 삼성전자 검색 결과를 반환한다.
2. 발행 시각과 수집 시각을 구분한다.
3. 원문 URL이 포함된다.
4. 결과 없음과 API 실패를 구분한다.
5. 중복 기사 기준이 문서화된다.

## 구조

```text
news_mcp/
├─ server.py                # 진입점: FastMCP 생성 + Tool 등록 + /health (로직 없음)
├─ app/
│  ├─ core/config.py        # .env → NewsConfig
│  ├─ schemas/news.py       # Tool 입출력 TypedDict (계약 필드와 동일)
│  ├─ clients/naver_news.py # NAVER API HUB 뉴스 검색 API 호출
│  ├─ services/news.py      # 원본 응답 → 계약 형식 변환, 중복·비관련 기사 제거
│  ├─ services/mock.py      # Client ID/Secret 없을 때 쓰는 표본 응답
│  └─ tools/news.py         # search_news 입력 검증 + register_news_tools
├─ tests/                   # 가짜 client/payload로 네트워크 없이 검증 (pytest)
├─ .env.example
└─ requirements.txt
```

요청 흐름: MCP Client → `tools/news.py`(입력 검증) → `services/news.py` → `clients/naver_news.py` → NAVER API HUB. 응답은 역순으로 돌아오며 services에서 중복 제거·관련성 필터링 후 계약 형식으로 맞춘다.

NAVER API HUB 뉴스 검색 API는 응답에 언론사명(`publisher`)을 주지 않는다(`title`, `originallink`, `link`, `description`, `pubDate`만 제공). 따라서 `publisher`는 `originallink` 도메인으로 임시 대체한다(예: `thebell.co.kr`). 정확한 언론사명이 필요해지면 도메인→언론사 매핑 테이블을 추가한다.

중복·관련성 판단 기준:
- 중복: `source_url`(없으면 제목)이 같은 기사는 첫 기사만 남긴다.
- 관련성: 제목·요약에 `company_name`이 포함되지 않으면 낮음으로 보고 결과에서 제외한다.
- 기간: `published_at`이 `lookback_days` 이전이면 제외한다.

손대는 위치:
- 계약 필드 추가 → `schemas/news.py` + `services/news.py`의 map 함수 + `shared/contracts/news/README.md`
- 원본 API 변경 → `clients/naver_news.py`만
- Tool 추가 → `tools/news.py`에 함수 작성 후 `register_news_tools`에 한 줄 등록

## 실행법

```bash
cd mcp_servers/news_mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # NAVER_NEWS_CLIENT_ID/SECRET 비우면 Mock 응답, 채우면 실데이터
python server.py
curl http://127.0.0.1:8021/health
```

MCP Client는 `http://127.0.0.1:8021/mcp`로 접속해 `search_news`를 호출한다.
