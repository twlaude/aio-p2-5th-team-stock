# 커뮤니티 MCP 서버 가이드

## 목적

태웅님이 운영하는 커뮤니티 데이터 서버에서 종목 관련 게시글과 반응을 받아 시장 참여자들이 어떤 내용을 이야기하는지 정리한다.

## 위치와 역할

커뮤니티 원본 수집 서버가 별도로 존재한다면 이 MCP 서버는 그 서버와 MCP Client 사이의 어댑터 역할을 한다.

```text
태웅님 커뮤니티 데이터 서버
  → Community MCP
  → MCP Client
```

## 담당 범위

- 기업명 또는 종목 코드로 게시글 조회
- 게시글·댓글·작성 시각 정리
- 반복 글과 광고성 데이터 처리
- 긍정·부정·중립 반응 집계
- 많이 언급된 주제 추출
- 분석 기간과 표본 수 반환
- 15분 공포탐욕 지수 반환

## 확정 Tool

```text
get_community_reaction
get_fear_greed_index
```

입출력은 `shared/contracts/community/README.md`를 따른다. 게시글 검색과 주제 추출은 Community MCP 내부 Service가 담당하며 원문 조회 Tool로 외부에 노출하지 않는다.

## 반환해야 할 핵심 정보

```text
period
sample_size
positive_count
neutral_count
negative_count
top_topics
representative_posts
source
collected_at
fgi_latest
```

## 환경변수 계획

```text
COMMUNITY_API_URL
COMMUNITY_API_TOKEN
COMMUNITY_MCP_HOST=0.0.0.0
COMMUNITY_MCP_PORT=8023
COMMUNITY_LOOKBACK_DAYS=7
COMMUNITY_RESULT_LIMIT=100
```

## 주의사항

- 커뮤니티 의견을 사실로 표현하지 않는다.
- 일부 게시글을 전체 투자자 의견처럼 표현하지 않는다.
- 표본 수와 분석 기간을 함께 제공한다.
- 원문 저장·재사용 범위는 데이터 제공 방식과 이용 조건을 확인한다.

## Mock 단계

삼성전자 게시글 반응을 표본 데이터로 만들어 MCP Client가 요구하는 필드와 연결을 먼저 검증한다.

## 완료 기준

1. 종목별 반응을 반환한다.
2. 분석 기간과 표본 수가 표시된다.
3. 의견과 사실을 구분한다.
4. 원본 서버 장애 상태를 반환한다.
5. MCP Client가 다른 MCP 결과와 함께 사용할 수 있는 공통 형식을 따른다.
6. `get_fear_greed_index`가 최신 15분 공포탐욕 지수와 표본 부족 경고를 반환한다.

## 실행법

```bash
cd mcp_servers/community_mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # COMMUNITY_API_TOKEN 비우면 Mock 응답, 채우면 실데이터
python server.py
curl http://127.0.0.1:8023/health
```

MCP Client는 `http://127.0.0.1:8023/mcp`로 접속해 `get_community_reaction`과 `get_fear_greed_index`를 호출한다.
