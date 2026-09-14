# Disclosure MCP Tool 계약

> **한눈에**
> 공시·최신 연간 사업보고서를 조회합니다.
> 검색 시점 최근 30일 목록과 상세 1~2건을 조회합니다.
> 보고서는 관련 청크(문서 조각)만 LLM(언어 모델)에 보냅니다.

## 연결

- MCP 주소: `http://DISCLOSURE_MCP_HOST:8022/mcp`
- 제공처: OpenDART
- 최신 연간 사업보고서 1개는 미리 저장·임베딩(검색용 수치 변환)합니다.

## Tool 1: `get_recent_disclosures`

입력:

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930",
  "lookback_days": 30,
  "limit": 20,
  "disclosure_types": ["A", "B", "I"]
}
```

`disclosure_types`: DART 코드 `A`~`J` 배열, 생략 시 `A`(정기공시)만 조회합니다(2026-09-04 팀 결정). `mcp_client`는 뉴스·커뮤니티 이슈 근거 판정 때만 비정기 공시를 명시합니다. 유형별 DART 요청 후 접수번호로 중복 제거합니다.

출력 핵심 필드:

```json
{
  "status": "success",
  "disclosures": [
    {
      "report_name": "공시명",
      "receipt_number": "접수번호",
      "published_at": "2026-09-01T00:00:00Z",
      "document_type": "disclosure",
      "disclosure_kind": "major",
      "source_url": "https://dart.fss.or.kr/..."
    }
  ],
  "collected_at": "2026-09-01T09:00:00Z"
}
```

`disclosure_kind`: 기존 저장 분류인 `periodic`·`major`·`other` 중 하나입니다.

## Tool 2: `get_disclosure_detail`

입력: `receipt_number`. 출력: 제목·핵심 내용·공식 URL. Agent는 최근 목록의 질문 관련 공시 최대 2건에만 씁니다.

## Tool 3: `search_annual_report`

입력:

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930",
  "query": "반도체 사업의 주요 위험과 성장 계획",
  "top_k": 5,
  "min_score": 0.7
}
```

출력:

```json
{
  "status": "success",
  "report_name": "최신 사업보고서",
  "receipt_number": "접수번호",
  "report_year": 2025,
  "matched_passages": [
    {
      "section": "사업의 내용",
      "text": "질문과 관련된 보고서 일부",
      "score": 0.82
    }
  ],
  "filtered_out": 2,
  "source_url": "https://dart.fss.or.kr/...",
  "collected_at": "2026-09-01T09:00:00Z"
}
```

`top_k`: 최대 5. `min_score`: `0.0`~`1.0`, 기본 `0.0`은 기존 결과와 같습니다. `filtered_out`: 유사도 하한 미만으로 제외한 청크 수.
보고서가 있고 모든 청크가 하한 미만: `status: "success"`, `matched_passages: []`. 보고서 없음과 구분합니다.
