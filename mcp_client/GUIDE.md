# MCP Client 통합 서버 가이드

## 역할

MCP Client는 Backend가 호출하는 독립 FastAPI 서버이면서 Price·News·Disclosure·Community MCP의 통합 Client다.

```text
Backend
  → MCP Client Workflow
      ├─ Price MCP
      ├─ News MCP
      ├─ Disclosure MCP
      └─ Community MCP
  → 규칙 기반 관심 온도·근거 수준 계산
  → Luna Agent 설명
  → Backend
```

지원 기업 20개 확인, 로그인, 투자 성향 저장은 Backend가 담당한다. MCP Client는 원본 증권·뉴스·DART·커뮤니티 API를 직접 호출하지 않는다.

## 실행 흐름

1. `POST /internal/v1/common-analyses` 요청을 검증한다.
2. 현재가, 최근 뉴스, 정기공시, 최근 30일 주요 비정기 공시, 최신 사업보고서, 커뮤니티 반응을 병렬 조회한다.
3. 실패한 Tool은 기록하고 성공한 자료는 유지한다. 현재가 실패는 Backend가 처리할 수 있도록 요청 자체를 실패시킨다.
4. Python 규칙이 0~100 관심 온도와 근거 수준을 계산한다.
5. Luna Agent가 최근 공시 상세를 더 볼지 판단한다.
6. Runtime은 허용된 Tool과 기본 목록에 포함된 접수번호인지 검증한다.
7. Luna가 추천 없이 한 줄 평과 세 자료 요약을 JSON Schema로 반환한다.
8. 회원이면 Backend가 보낸 투자 성향으로 확인 순서를 추가한다.

## 기본 조회

```text
get_stock_quote
search_news                 최근 7일, 최대 10건
get_recent_disclosures      정기공시 최근 180일, 최대 20건
get_material_disclosures    최근 30일 B/C/D/E/I 공시, 최대 50건
search_annual_report        고정 검색문, 최대 5개 구절
get_community_reaction      최근 7일, 최대 100개 표본
```

Community 기본 응답에 `fgi_latest`가 포함되므로 `get_fear_greed_index`를 중복 호출하지 않는다.

## Agent 경계

기본 조회는 AI가 아니라 Workflow가 항상 실행한다. Agent에 허용된 추가 Tool은 읽기 전용 `get_disclosure_detail` 하나다.

- 기본 최근 공시 결과에 포함된 접수번호만 허용
- 동일 접수번호 반복 호출 차단
- 상세 공시 최대 2건
- Agent 최대 3단계
- 매수·매도·가격 방향 예측 금지
- 내부 추론, Prompt, API Key를 Trace에 저장하지 않음

조회 Tool뿐이므로 Human Approval은 요구하지 않는다. 추후 저장·전송·주문 Tool이 생기면 별도 승인 정책을 추가한다.

## 시장 관심 온도 v2 기준

```text
20일 평균 대비 거래량       30점
기간 내 관련 뉴스 기사 수   25점
이전 28일 대비 커뮤니티 활동 25점
공포·탐욕 강도              20점
```

입력이 없는 항목은 배점에서 제외하고 가용 배점 합을 기준으로 0~100점으로
재정규화한다. `weight_covered`는 실제 계산에 포함된 항목의 배점 합이다. 주가
등락률과 공시·보고서 수는 관심 온도에 가점을 주지 않는다.

```text
0~19    관심 낮음
20~39   관심 다소 낮음
40~59   보통
60~79   관심 높음
80~100  관심 매우 높음
```

이 계산은 수익률이나 상승 가능성을 의미하지 않는다. 라벨 구간은 기존 규칙을 유지한다.

근거 수준은 커뮤니티 기대 3개·우려 2개와 제목에 정식 회사명이 들어간 뉴스 2개에서 현재 이슈를 뽑은 뒤, 최근 30일 주요 비정기 공시명과 규칙 사전으로 연결해 정한다. 연결 공시가 있으면 `high`, 연결은 없지만 주요 공시가 있으면 `medium`, 주요 공시가 없거나 조회에 실패하면 `low`다. 임베딩·유사도 하한과 자료 종류 수·커뮤니티 표본 수는 이 판정에 쓰지 않는다. 응답은 연결 공시 `matched`, 미연결 이슈 `unmatched`, 주요 공시 수 `material_count`를 함께 제공한다.

## Backend 요청

```json
{
  "request_id": "uuid",
  "company": {"company_name": "삼성전자", "stock_code": "005930"},
  "investment_profile": null,
  "requested_at": "2026-09-04T00:00:00Z"
}
```

자유 질문형 서비스가 아니므로 `question`, `date_range`는 받지 않는다.

## 진행 이벤트

`BACKEND_EVENT_URL`이 설정되면 Workflow 진행 메타데이터를 Backend에 전달한다. 설정되지 않으면 분석은 그대로 실행되며 이벤트는 외부로 전송하지 않는다.

```text
workflow_started
collection_started
tool_started
tool_completed
tool_failed
llm_started
llm_completed
workflow_completed
workflow_failed
```

MCP 원문과 사용자 개인정보는 이벤트로 보내지 않는다. Backend의 이벤트 API와 Redis 저장 규격은 기화님·태웅님 협의 후 URL만 연결한다.

## 실행

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

```text
API:    http://localhost:8010/internal/v1/common-analyses
Health: http://localhost:8010/health
Status: http://localhost:8010/internal/v1/mcp-status
```

`LLM_PROVIDER=mock`은 OpenAI 비용 없이 서버 연결과 화면 규격을 확인할 때만 사용한다. 실제 발표 연동은 `LLM_PROVIDER=openai`와 `OPENAI_API_KEY`를 사용한다.

## Docker

```powershell
docker build -t stock-mcp-client .
docker run --env-file .env -p 8010:8010 stock-mcp-client
```

## 테스트

```powershell
pytest -q
```
