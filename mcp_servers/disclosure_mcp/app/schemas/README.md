# Disclosure Schemas

Pydantic 등으로 MCP Tool의 입력·출력과 내부 문서 모델을 정의한다. 공개 Tool 계약의 기준은 `shared/contracts/disclosure/README.md`다.

`re.py`는 OpenDART 원본 응답 전용 스키마다. DART의 `snake_case` 필드명과
상태값을 그대로 보존하며, 외부 MCP Tool 응답으로 그대로 반환하지 않는다.

## 주요 모델

- `CompanyIdentity`: `company_name`, `stock_code`, 내부 전용 `corp_code`
- `DisclosureItem`: `report_name`, `receipt_number`, `published_at`, `document_type`, `source_url`
- `DisclosureDetail`: 공시 메타데이터, 핵심 내용, 공식 원문 URL
- `AnnualReportChunk`: 보고서·접수번호·사업연도·섹션·원문·유사도·출처
- `ToolResponse`: `status`, 데이터, `collected_at`, 오류 정보
- `DartCorpCode`, `DartDisclosureRecord`: `corpCode.xml`, `list.json` 원본 항목
- `DartDisclosureListResponse`, `DartDocument`: DART 목록·원문 처리용 내부 값

## 데이터 규칙

- 접수번호는 문자열 14자리로 보존한다. 숫자로 변환하지 않는다.
- `published_at`과 `collected_at`은 구분하고 ISO 8601 형식으로 반환한다.
- `source_url`은 DART 공식 공시뷰어 URL만 사용한다.
- 기업 고유번호는 서버 내부 식별자이며 별도 MCP Tool로 공개하지 않는다.
