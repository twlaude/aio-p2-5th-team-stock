# Disclosure MCP Tools

MCP Client에 공개하는 Tool만 정의한다. 기업 고유번호 조회는 `company_resolver`가 내부적으로 수행하므로 공개 Tool가 아니다.

## `get_recent_disclosures`

최근 공시 목록을 반환한다.

- 입력: `company_name`, `stock_code`, 선택값 `lookback_days`, `limit`
- 기본 조회기간: 30일
- 출력: 공시명, 접수번호, 발행일, 문서 유형, DART 원문 URL, 수집 시각

## `get_disclosure_detail`

접수번호 하나의 상세 공시를 반환한다.

- 입력: `receipt_number`
- 출력: 공시 제목, 핵심 내용, 공식 원문 URL, 발행일과 수집 시각
- 원문은 표를 `셀 | 셀` 형태로 평탄화하고 최대 3,000자만 반환한다. 전체 길이와
  잘림 여부는 `total_chars`, `content_truncated`으로 전달한다.
- 사용 제한: Agent는 최근 공시 중 질문과 직접 관련된 최대 2건만 상세 조회한다.

## `search_annual_report`

최신 사업보고서에서 질문과 관련된 원문 구절을 검색한다.

- 입력: `company_name`, `stock_code`, `query`, 선택값 `top_k`
- 동작: 기업 식별 → 최신 사업보고서 확인 → 필요 시 온디맨드 색인 → 관련 청크 검색
- 출력: 보고서명, 접수번호, 사업연도, 매칭 문단, DART URL, 수집 시각
- `top_k`: 최대 5. 보고서 전체를 반환하지 않는다.

자세한 JSON 필드와 예시는 `shared/contracts/disclosure/README.md`를 따른다.

## `search_periodic_report`

사업·반기·분기보고서를 공통으로 검색한다.

- 입력: `stock_code`, `query`, `report_type` (`annual` | `semi_annual` | `quarterly`)
- 선택 입력: `company_name`, `report_year`, `top_k`
- 출력: 보고서 유형·연도·관련 원문 청크·DART 출처
