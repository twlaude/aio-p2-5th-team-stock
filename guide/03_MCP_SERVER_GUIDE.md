# MCP Server 개발 방향 제안서

> 이 문서는 팀 회의를 위한 MCP Server 설계 예시입니다. 실제 Tool 목록과 외부 데이터 제공처는 접근 가능성·비용·이용 조건을 확인한 뒤 확정합니다.

## 1. MCP Server의 역할

MCP Server는 AI Agent가 사용할 수 있는 주식 정보 도구를 제공한다.

Backend 또는 Agent가 특정 데이터 제공처의 요청 방식과 DB 구조를 모두 알 필요가 없도록, MCP Tool이 입력과 출력을 표준화한다.

예를 들어 Agent는 `get_market_snapshot`이라는 Tool만 호출하고, Tool 내부에서 어떤 시세 API를 사용하는지는 알 필요가 없다.

## 2. MCP가 담당할 영역

- 종목명과 종목코드 연결
- 가격·거래량 조회
- 개인·외국인·기관 수급 조회
- 뉴스 검색
- DART 공시·재무 조회
- 커뮤니티 데이터 조회와 요약
- pgvector RAG 검색
- 사용자 투자 메모 검색
- 필요할 경우 데이터 수집·임베딩 작업 실행

로그인, 사용자 권한, 화면 응답 조립은 Backend가 담당한다.

## 3. 폴더 구조 예시

현재 `clients`, `schemas`, `services`, `tools` 구분을 유지한다.

```text
mcp_server/stock_mcp/
├─ .env.example
├─ requirements.txt
├─ stock_server.py              # MCP 생성 및 Tool 등록
└─ app/
   ├─ core/
   │  ├─ config.py              # DB·API·임베딩 설정
   │  ├─ database.py
   │  └─ logging.py
   ├─ clients/
   │  ├─ market_client.py       # 시세·수급 제공처
   │  ├─ news_client.py
   │  ├─ dart_client.py
   │  ├─ community_client.py
   │  ├─ embedding_client.py
   │  └─ vector_store.py
   ├─ schemas/
   │  ├─ stock.py
   │  ├─ market.py
   │  ├─ news.py
   │  ├─ disclosure.py
   │  ├─ community.py
   │  ├─ retrieval.py
   │  └─ common.py
   ├─ services/
   │  ├─ stock_service.py
   │  ├─ market_service.py
   │  ├─ news_service.py
   │  ├─ disclosure_service.py
   │  ├─ community_service.py
   │  ├─ retrieval_service.py
   │  └─ ingestion_service.py
   └─ tools/
      ├─ stock_tools.py
      ├─ market_tools.py
      ├─ news_tools.py
      ├─ disclosure_tools.py
      ├─ community_tools.py
      └─ rag_tools.py
```

### 계층 역할

- `tools`: MCP에 공개할 함수, 설명, 입출력 정의
- `services`: 데이터 조합, 정규화, 계산, 검색 규칙
- `clients`: 외부 API·DB·임베딩 제공처 연결
- `schemas`: Tool 입력과 출력 형식
- `core`: 환경설정, DB 연결, 공통 로그

Tool 함수 안에 긴 외부 API 처리나 SQL을 직접 작성하지 않는 방향을 권장한다.

## 4. Tool 목록 예시

### 4.1 종목 검색

`search_stock`

- 입력: 기업명 또는 종목코드
- 출력: 종목명, 종목코드, 시장, 업종, DART 기업번호
- 역할: 이후 모든 Tool이 공통으로 사용할 종목 식별자 확정

### 4.2 가격·거래량

`get_market_snapshot`

- 입력: 종목코드
- 출력: 현재가, 전일 대비, 등락률, 거래량, 기준 시각

`get_price_history`

- 입력: 종목코드, 시작일, 종료일, 간격
- 출력: 가격·거래량 시계열

### 4.3 투자자별 수급

`get_investor_flow`

- 입력: 종목코드, 기간
- 출력: 개인·외국인·기관 순매수와 추이
- 주의: 데이터 제공처가 제공하는 실제 집계 주기와 기준을 함께 반환

### 4.4 뉴스

`search_stock_news`

- 입력: 종목코드, 기간, 키워드, 개수
- 출력: 제목, 요약, 언론사, 발행 시각, URL, 주요 주제

뉴스 검색 결과는 동일 보도자료의 반복 기사를 가능한 범위에서 묶고, 원문 출처를 유지한다.

### 4.5 DART 공시·재무

`search_disclosures`

- 입력: 종목코드, 기간, 공시 종류
- 출력: 공시 제목, 접수일, 접수번호, 요약, 원문 주소

`get_financial_metrics`

- 입력: 종목코드, 연도, 분기
- 출력: 매출, 영업이익, 순이익 등 확정된 수치

`retrieve_disclosure_evidence`

- 입력: 종목코드, 질문, 문서 종류, top_k
- 출력: 관련 공시 청크와 출처

### 4.6 커뮤니티

`get_community_sentiment`

- 입력: 종목코드, 기간
- 출력: 긍정·부정·중립 비율, 게시글 수, 주요 기대·우려 주제, 기준 시각

`retrieve_community_topics`

- 입력: 종목코드, 질문, 기간
- 출력: 질문과 관련된 커뮤니티 요약 청크

커뮤니티 내용은 사실이 아닌 시장 반응으로 표시한다. 특정 커뮤니티의 실제 데이터 확보가 어려울 경우 Tool의 출력 계약은 유지하고 데이터 제공처만 교체할 수 있어야 한다.

### 4.7 RAG와 사용자 메모

`retrieve_stock_evidence`

- 입력: 종목코드, 질문, 문서 종류 목록, 기간, top_k
- 출력: 뉴스·공시·커뮤니티·리포트 근거

`retrieve_user_notes`

- 입력: 사용자 ID, 종목코드, 질문, top_k
- 출력: 사용자의 관련 매수 근거·우려·확인 조건

MCP Server는 사용자 ID가 포함된 요청에서 권한이 검증되었다고 무조건 가정하지 않고, Backend와 인증 정보 전달 방식을 합의해야 한다.

## 5. Tool 출력 공통 필드

모든 Tool 결과에 가능한 범위에서 다음 정보를 포함한다.

- `status`: 성공, 일부 성공, 결과 없음, 실패
- `stock_code`
- `observed_at`: 데이터 기준 시각
- `source`
- `source_url` 또는 원문 식별자
- `data`: 실제 결과
- `warnings`: 지연 데이터, 누락, 추정 여부
- `error_code`: 실패 시 분류 가능한 코드

Agent가 서로 다른 Tool 결과를 비교하려면 기준 시각과 출처가 반드시 필요하다.

## 6. RAG 검색 규칙

RAG는 벡터 유사도 검색만 의미하지 않는다. 질문에 따라 다음 방식을 구분한다.

| 질문 | 검색 방식 |
|---|---|
| 현재가·날짜·수치 | 외부 API 또는 SQL |
| 특정 공시 제목·정확한 키워드 | 메타데이터·키워드 검색 |
| 위험 요소·시장 우려 같은 의미 검색 | pgvector 유사도 검색 |
| 짧은 단일 문서 요약 | 문서 전체 또는 필요한 부분 직접 전달 |

벡터 검색은 다음 순서를 따른다.

1. `stock_code`로 종목을 제한한다.
2. `doc_type`으로 뉴스·공시·커뮤니티·메모를 제한한다.
3. 사용자 메모는 `user_id`를 추가로 제한한다.
4. 기간 조건이 있으면 `published_at`을 제한한다.
5. 제한된 범위에서 유사도 top-k를 검색한다.

## 7. 문서 수집·임베딩 방향

```text
원문 수집
  → 종목코드 연결
  → 본문 정제
  → 문서 중복 확인
  → 문서 종류·출처·발행일 저장
  → 청킹
  → 임베딩
  → rag_chunks 저장
```

필요한 메타데이터 예시:

- 종목코드
- 문서 종류
- 원문 식별자
- 제목
- 출처
- 발행일
- 수집일
- 청크 번호
- 본문 해시
- 임베딩 모델
- 원문 URL
- 수집 버전

임베딩 모델을 바꾸면 기존 데이터와 벡터 차원이 달라질 수 있으므로 프로젝트에서 하나로 통일한다.

## 8. 시장 심리 계산 책임

시장 심리 온도를 LLM이 임의로 계산하지 않도록 한다.

MCP의 `community_service` 또는 별도 분석 서비스가 다음 정형 수치를 계산하고, LLM은 결과를 설명한다.

- 긍정·부정·중립 비율
- 기간 대비 게시글 증가율
- 주요 기대·우려 키워드
- 가격·거래량 변화
- 개인·외국인·기관 수급 방향
- 긍정·부정 뉴스 흐름

근거 강도는 공시 존재 여부, 공식 수치, 출처, 최신성, 여러 자료의 일치 여부 등을 바탕으로 계산 기준을 별도로 합의한다.

## 9. MCP Server 분리 기준

MVP에서는 하나의 `stock_mcp` 서버 안에 여러 Tool을 두는 방향이 단순하다.

다음 조건이 생기면 서버 분리를 검토할 수 있다.

- 데이터 제공처별 인증과 운영 환경이 크게 다름
- 뉴스·커뮤니티 수집 작업이 조회 Tool에 영향을 줌
- 특정 Tool만 별도 확장해야 함
- 팀원이 컴퓨터별로 서버를 분담해야 함
- 장애 범위를 분리할 필요가 있음

가능한 확장 예시는 `market_mcp`, `document_mcp`, `community_mcp`지만 처음부터 분리할 필요는 없다.

## 10. 성능과 안정성 원칙

- 외부 요청은 타임아웃을 지정한다.
- 가능한 독립 조회는 비동기로 병렬 처리한다.
- 외부 API 응답을 내부 공통 Schema로 변환한다.
- 중복 문서는 본문 해시와 원문 식별자로 방지한다.
- 데이터가 없을 때 LLM이 값을 만들지 않도록 명확한 상태를 반환한다.
- Tool 하나가 실패해도 다른 Tool 결과를 사용할 수 있게 한다.
- 조회 결과에는 항상 데이터 기준 시각을 포함한다.
- 개발 초기에는 최적화보다 입출력 계약과 정확성을 우선한다.

## 11. MCP 개발 순서 제안

1. 현재 `ping` Tool로 Backend 연결 확인
2. 샘플 `search_stock` Tool
3. 샘플 `get_market_snapshot` Tool
4. DB 조회 Tool
5. 실제 시세·수급 Client
6. 뉴스와 DART Tool
7. `rag_chunks` 검색 Tool
8. 커뮤니티 분석 Tool
9. 사용자 메모 검색 Tool
10. Tool 오류·출처·기준 시각 표준화
11. 필요할 경우 MCP 서버 분리

## 12. MCP 회의 질문

- 시세와 수급을 어떤 제공처에서 받을 수 있는가?
- 뉴스 본문을 저장할 수 있는가, 제목·요약만 사용할 것인가?
- 커뮤니티 데이터 확보가 가능한가?
- MCP 서버를 하나로 시작할 것인가?
- Backend에서 MCP로 사용자 권한을 어떻게 전달할 것인가?
- 시장 심리 계산을 수집 단계와 조회 단계 중 어디에서 수행할 것인가?
- Tool 출력의 공통 Schema를 무엇으로 할 것인가?
- 실패·지연 데이터에 대한 경고 형식을 어떻게 통일할 것인가?

