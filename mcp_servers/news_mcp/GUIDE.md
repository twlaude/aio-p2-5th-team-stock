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

## 목표 구조

```text
news_mcp/
├─ server.py       # 진입점 (FastMCP 생성 + Tool 등록)
├─ app/
│  ├─ tools/       # MCP Tool
│  ├─ services/    # 기사 정제·중복 제거·요약
│  ├─ clients/     # 뉴스 API 연결
│  ├─ schemas/     # Tool 입출력
│  └─ core/        # 설정·로그
├─ tests/
├─ .env.example
├─ requirements.txt
└─ GUIDE.md
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
