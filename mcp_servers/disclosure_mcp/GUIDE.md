# 전자공시 MCP 서버 가이드

## 목적

DART 공시와 기업보고서를 조회하고, 긴 문서는 RAG로 검색하여 MCP Client가 지정한 내부 분석 주제와 관련된 공식 근거를 반환한다.

## 담당 범위

- 기업명에서 DART 기업 고유번호 확인
- 공시 목록 조회
- 공시 상세정보와 원문 URL 제공
- 기업보고서 수집
- 긴 문서 청킹과 임베딩
- 종목·문서 종류를 먼저 필터링한 뒤 벡터 검색

## 확정 Tool

```text
get_recent_disclosures
get_disclosure_detail
search_annual_report
```

입출력은 `shared/contracts/disclosure/README.md`를 따른다. 기업 고유번호 확인은 서버 내부 Service가 담당하고 별도 공개 Tool로 만들지 않는다.

## RAG 처리 흐름

```text
DART·기업보고서
  → 원문 저장
  → 문서 정리
  → 청킹
  → 임베딩
  → pgvector 저장
  → 종목·문서 종류 선필터
  → 관련 청크 검색
```

## 반환해야 할 핵심 정보

```text
report_name
receipt_number
published_at
document_type
summary
matched_passages
source_url
collected_at
```

## 목표 구조

```text
disclosure_mcp/
├─ server.py       # 진입점 (FastMCP 생성 + Tool 등록)
├─ app/
│  ├─ tools/       # MCP Tool
│  ├─ services/    # 공시 정제·요약
│  ├─ rag/         # 청킹·임베딩·검색
│  ├─ clients/     # DART API·DB 연결
│  ├─ schemas/     # Tool 입출력
│  └─ core/        # 설정·로그
├─ tests/
├─ .env.example
├─ requirements.txt
└─ GUIDE.md
```

## 환경변수 계획

```text
DART_API_KEY
DART_API_URL
DATABASE_URL
EMBEDDING_PROVIDER
EMBEDDING_MODEL
DISCLOSURE_MCP_HOST=0.0.0.0
DISCLOSURE_MCP_PORT=8022
DART_LOOKBACK_DAYS=30
ANNUAL_REPORT_TOP_K=5
```

## Memory와의 구분

전자공시와 기업보고서는 사용자 Memory가 아니다. 이는 종목 분석을 위한 RAG 문서이며 모든 사용자에게 동일한 공식 근거로 사용한다.

## Mock 단계

삼성전자 공시 2~3개와 기업보고서 청크를 고정 데이터로 준비하여 검색 결과 형식부터 검증한다.

## 완료 기준

1. 기업명과 DART 기업번호를 연결한다.
2. 공시 접수번호와 원문 URL을 유지한다.
3. MCP Client가 지정한 분석 주제와 관련된 문서 부분을 반환한다.
4. 문서 발행일과 수집일을 구분한다.
5. 공식 자료와 LLM 해석을 구분한다.
