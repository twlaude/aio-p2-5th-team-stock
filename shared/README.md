# shared — 서비스가 함께 쓰는 고정 자산

| 파일 | 쓰는 곳 | 내용 |
|---|---|---|
| `supported_companies.json` | Backend(지원 여부 확인), Disclosure MCP(`sync_companies.py`), Frontend 목록, 계약 테스트 | KOSPI 시가총액 상위 20종목의 기업명·6자리 종목코드 스냅샷 |

종목을 바꾸면 이 파일만 고치고 `python -m pytest -q tests/contract/`로 20종목 유일성 계약을 확인합니다. 서비스 간 요청·응답 계약 문서는 `docs/specs/contracts/`에 있습니다.
