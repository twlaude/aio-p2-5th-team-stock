# Disclosure MCP Core

서버 설정, 의존성 초기화, 로깅과 공통 오류 처리를 둔다.

## 환경변수

```dotenv
DART_API_KEY=                 # OpenDART에서 발급한 40자리 인증키
DART_API_URL=https://opendart.fss.or.kr/api
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/stock_db
EMBEDDING_PROVIDER=
EMBEDDING_MODEL=
DISCLOSURE_MCP_HOST=0.0.0.0
DISCLOSURE_MCP_PORT=8022
DART_LOOKBACK_DAYS=30
ANNUAL_REPORT_TOP_K=5
```

- 실제 키는 로컬 `.env` 또는 배포 환경의 비밀 설정에만 둔다. `.env`는 Git에 올리지 않는다.
- `ANNUAL_REPORT_TOP_K`의 최대값은 Tool 계약에 맞춰 5로 제한한다.
- 설정 오류는 서버 시작 시 명확히 실패시킨다. 키 값 자체는 절대 로그에 기록하지 않는다.

## 상태 구분

- `success`: 정상 조회 또는 검색 완료
- `not_found`: 기업, 공시 또는 질문과 일치하는 보고서 청크가 없음
- `external_error`: OpenDART·임베딩·DB 연결 또는 요청 제한 문제
- `configuration_error`: 필수 환경변수가 없거나 잘못됨
